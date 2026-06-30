import os
import queue
import torch
import threading
from datetime import datetime 
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler # 引入 DPM++ 调度器 替代原来的 Eular， 大幅提升性能，现在实测2080ti 1s一张 （我怎么记得还有dpm2++ karras?)
from modules import config
import torch._dynamo
from diffusers import AutoencoderTiny
torch._dynamo.config.suppress_errors = True


class GalgameArtEngine:
    def __init__(self):
        self.device = "cuda"
        self.pipe = StableDiffusionPipeline.from_single_file('./models/anything-v5.safetensors', torch_dtype=torch.float16)

        self.pipe.vae = AutoencoderTiny.from_pretrained("madebyollin/taesd", torch_dtype=torch.float16).to("cuda")
        self.pipe.safety_checker = None
        
        # 根据启动器配置动态应用显存策略
        if getattr(config, 'low_vram_mode', False):
            print(">>> [ArtEngine] 已启用低显存模式 (CPU Offload)，速度较慢但防爆显存")
            self.pipe.enable_model_cpu_offload()
        else:
            print(">>> [ArtEngine] 已启用满血模式 (GPU 全载入)，速度极快")
            self.pipe.to(self.device)

        #DPM++ 2M Karras
        self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            self.pipe.scheduler.config,
            use_karras_sigmas=True,
            algorithm_type="dpmsolver++"
        )

        self.pipe.unet.to(memory_format=torch.channels_last)
        if hasattr(self.pipe, "vae"):
            self.pipe.vae.to(memory_format=torch.channels_last)
            
        self.pipe.enable_vae_slicing()
        self.pipe.enable_vae_tiling()
        
        self.base_prompt_prefix = self.load_pprt()
        self.image_cache = {} 
        self.generation_queue = queue.Queue() 

        os.makedirs("outputs", exist_ok=True)

    def load_pprt(self):
        default = "best quality, masterpiece, highres, 1girl, asuka langley, vibrant colors, anime style, soft lighting, sharp focus, looking at viewer, upper body, "
        try:
            if os.path.exists("config.pprt"):
                with open("config.pprt", "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    return content if content else default
        except Exception as e:
            print(f"读取 PPRT 失败: {e}")
        return default

    def generate_async(self, mood_prompt, bg_prompt, time_str="afternoon"):
        cache_key = f"{mood_prompt}_{bg_prompt}_{time_str}"
        if cache_key in self.image_cache:
            self.generation_queue.put(self.image_cache[cache_key])
            return None
        
        def _task():
            time_modifiers = {
                "morning": "morning light, soft sunlight, clear sky, morning dew, refreshing",
                "noon": "bright daylight, vivid colors, strong shadows, high contrast",
                "afternoon": "afternoon, golden hour, warm lighting, sunset vibes, beautiful lighting",
                "evening": "evening, sunset, orange sky, dusky, long shadows",
                "night": "night, dark, street lights, moonlight, night atmosphere, cinematic lighting"
            }
            time_tag = time_modifiers.get(time_str.lower(), "")
            prompt = f"{self.base_prompt_prefix}, {bg_prompt}, {mood_prompt}, {time_tag}"
            
            negative_prompt = (
                "(worst quality, low quality:1.4), (bad anatomy), (deformed limbs), "
                "bad hands, missing fingers, extra digit, fewer digits, cropped, ruined, text, "
                "watermark, signature, username, error, blurry, jpeg artifacts, bad feet, "
                "poorly drawn hands, poorly drawn face, mutation, extra limbs, extra arms, "
                "extra legs, malformed limbs, mutated hands, fused fingers, too many fingers, "
                "long neck, cross-eyed, mutated, ugly, disfigured, gross proportions, malformed, "
                "cloning, duplicate, multiple people, multiple girls, solo focus anomaly, severed limbs"
            )
            if not config.r18_mode:
                negative_prompt += ", nsfw"
            
            img = self.pipe(
                prompt, 
                negative_prompt=negative_prompt, 
                num_inference_steps=config.steps,   # 启动器传入的步数 (推荐拉到 15~20)
                guidance_scale=7.0,                 # DPM++ 建议用7.0吗？我问大佬说是的。
                width=896,
                height=504
            ).images[0]

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"outputs/img_{timestamp}_{hash(cache_key) % 10000}.png"
            img.save(filename)

            self.image_cache[cache_key] = (img, filename)
            self.generation_queue.put((img, filename))
            
        threading.Thread(target=_task, daemon=True).start()
        return None