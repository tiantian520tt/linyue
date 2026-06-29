import os
import queue
import torch
import threading
from diffusers import StableDiffusionPipeline, EulerAncestralDiscreteScheduler
from modules import config

class GalgameArtEngine:
    def __init__(self):
        self.device = "cuda"
        self.pipe = StableDiffusionPipeline.from_single_file('./models/anything-v5.safetensors', torch_dtype=torch.float16)
        self.pipe.safety_checker = None
        self.pipe.enable_model_cpu_offload()
        self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(self.pipe.scheduler.config)
        
        self.base_prompt_prefix = self.load_pprt()
        self.image_cache = {} 
        self.generation_queue = queue.Queue() 

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

    def generate_async(self, mood_prompt):
        if mood_prompt in self.image_cache:
            return self.image_cache[mood_prompt]
        
        def _task():
            prompt = f"{self.base_prompt_prefix}, {mood_prompt}"
            
            negative_prompt = (
                "lowres, bad anatomy, bad hands, text, error, missing fingers, "
                "extra digit, fewer digits, cropped, worst quality, low quality, "
                "normal quality, jpeg artifacts, signature, watermark, blurry"
            )
            if not config.r18_mode:
                negative_prompt += ", nsfw"
            
            img = self.pipe(
                prompt, 
                negative_prompt=negative_prompt, 
                num_inference_steps=config.steps,          
                guidance_scale=7.5,               
                width=768,
                height=512
            ).images[0]

            self.image_cache[mood_prompt] = img
            self.generation_queue.put(img)
            
        threading.Thread(target=_task, daemon=True).start()
        return None