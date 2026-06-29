# LinYue AiChat Game
林月，基于Stable Diffusion以及LLM实现的本地AI生成ACG游戏，拥有启动器指引进行部署，上手难度较低。<br/>
<a href="https://discord.gg/VseVN2aRBf">我们的Discord社区</a> 
<a href="https://qun.qq.com/universal-share/share?ac=1&svctype=5&tempid=h5_group_info&busi_data=eyJncm91cENvZGUiOiIxMDM4MzY4NDA4In0%3D" target="_blank">加入QQ群1038368408</a>
## 特色
### 内容完全由Ai生成
内容完全由Ai生成，你输入的文本，被Ai响应后生成文本和图片，一切都是未知的。<br/>
<img width="1240" height="716" alt="image" src="https://github.com/user-attachments/assets/48c867ae-3f32-4147-95f1-85ef8261e0f4" />

### 长记忆储存
算法优化，定期总结，经测试实现了150轮对话记忆不缺失！<br/>
<img width="1266" height="723" alt="image" src="https://github.com/user-attachments/assets/3b872845-b8cd-4f45-be22-d9e482a94fae" />

### 启动器设计
拥有启动器设计，智能检测和配置环境，允许一键设置参数。方便快捷。<br/>
<img width="479" height="589" alt="image" src="https://github.com/user-attachments/assets/612bd54a-39c5-4c0a-8e00-2f663f783d1c" />

### 服务端客户端分离设计
允许玩家使用云端服务器计算LLM模型，在本地运算Stable Diffusion模型，以分摊计算压力，同时改善使用体验！<br/>
你也可以在本地同时部署云端和客户端，完全本地化使用。<br/>
<img width="340" height="39" alt="image" src="https://github.com/user-attachments/assets/7432b3ba-be21-48fd-ba58-861ccb6997d4" />

### 智能音乐切换
客户端会根据LLM返回的Mood关键字，自动取切换本地音乐。<br/>
<img width="1269" height="710" alt="image" src="https://github.com/user-attachments/assets/6c861de3-b1cd-4bc2-a69d-4dcd8d0e2b28" />

### 友好内容创作设计
使用Modelfile和PPRT自定义形式，允许你自己构建自己的林月！自定义说话方式、自定义外观易如反掌。你可以在我们的Discord社区获得别人制作好的成品。<br/>
<img width="751" height="418" alt="image" src="https://github.com/user-attachments/assets/f4cfc64e-86c4-4679-aeee-3019124e98d4" />

### 未来展望
目前支持自定义LLM模型。未来将支持自定义Stable Diffusion模型，实现进一步自定义。另外，我们在未来将加入语音自定义模块可供开关，优化对话体验。最重要的是，本项目开源且永远免费！本地部署是我们开发者的本钱。<br/>
<img width="1239" height="578" alt="image" src="https://github.com/user-attachments/assets/98e6728b-fea3-4af8-8890-59fa7189b038" />

## 使用教程
### 1.基本环境手动配置
本地和服务器安装Python3.11,在服务器上安装Ollama最新版本（若只有本地，则只需要在本地安装二者）。<a href="https://ollama.com/">Ollama</a> <a href="https://www.python.org/downloads/release/python-3110/">Python 3.11</a><br/>
git拉取本仓库，下载模型anything-v5.safetensors存放在models文件夹下。<a href="https://huggingface.co/genai-archive/anything-v5/tree/main">抱脸链接</a>
### 2.运行启动器检测并配置环境
（服务端配置请到A. 关于服务端的配置）<br/>
使用python运行launcher.py<br/>
```bash
python launcher.py
```
<img width="442" height="466" alt="image" src="https://github.com/user-attachments/assets/336fe645-934f-41df-9bdb-3248ab2be070" />
(旧版本)
<img width="417" height="410" alt="image" src="https://github.com/user-attachments/assets/e32d99f5-6815-407a-8706-ebd856d43c87" />
(新版本)
<br/>接着启动器会检测环境并安装环境。如有报错，可截图发送到Discord社区进行求助。需要注意的是，此过程可能会安装一些AI大模型，这可能需要耗费很长的时间，请注意观察控制台。<br/>
配置成功后应如图所示，显示环境已就绪。<br/>
### 3.配置参数并启动
启动LinYue必须要有一个Modelfile，可选一个PPRT。这些都可以在Discord获得别人的成品。或者，你可以自行配置。首次启动一个Modelfile可能需要下载模型，请注意控制台。以及，游戏刚启动的第一句话初始化会很慢，请耐心等待。新版本更新后，Modelile改为在服务端配置，而不是在客户端配置!在构建完服务器后，你应该会得到一些ApiKey。你需要这些ApiKey才能访问你的服务器。<br/>
渲染步数推荐在15-20左右，如果你的PPRT较为复杂，可选20-30步。但无论如何，渲染最少不能少于15步，否则将出现画面崩坏。<br/>
启动后即可开始游戏。如果需要清除记忆，点击清除按钮。如果你想保存记忆并重新开始一段记忆，可以将本地的galgame_save.json文件改名保存，再次启动游戏就会生成新的记忆文件。另外，每次更换Modelfile，我建议你都要重置一次记忆文件，无论是删除还是备份改名。否则，可能会出现意外结果。<br/>
### A. 关于服务端的配置
服务端的启动方式：<br/>
使用命令行启动。（在Windows下）<br/>
```bash
cd server
python server.py --new-apikey
python server.py -p [端口] -modelile [文件路径]
```
必填参数 -p (端口) 以及 -modelfile (文件路径)。<br/>
执行--new-apikey后你将获得5个APIKEY。请记住它们，它们用于你在客户端验证身份。<br/>
其余可选的参数：<br/>
<img width="1039" height="269" alt="image" src="https://github.com/user-attachments/assets/7d9590f9-342f-4b8c-a6b1-28f34de754c6" />
如果你的电脑配置低，显存不足，只允许运行Stable Diffusion的话，使用云端服务器是最好的解决方案！你可以购买付费的小时计云GPU服务器来配置并保存镜像，这是一种可行方案。或者，去我们的Discord社区转转，那里可能有免费的公益服务器。
## 创作者指南
### Modelfile创作
Modelfile应该遵循Ollama规则，呈现如下格式。<br/>
```python
FROM 模型名

# 设置温度，0.7 是创造力与逻辑性的完美平衡点
PARAMETER temperature 0.7
# 限制上下文窗口，防止爆显存，8192 token 足够了
PARAMETER num_ctx 8192

# 注入极其严格的系统提示词（System Prompt）
SYSTEM """
你现在是一个Galgame游戏引擎的后台AI导演。
你的任务是扮演游戏女主角傲娇学妹，并控制游戏的视觉呈现。

【角色设定】
- 名字：林月
- 属性：典型的傲娇，嘴硬心软，明明很关心玩家（前辈），却总要用讽刺或不耐烦的语气掩饰。
- 习惯：紧张时会结巴，喜欢用“哼”、“笨蛋”作为口头禅。

【工作规范】
你必须且只能以 JSON 格式输出，绝对不要输出任何 markdown 标记、解释文本或多余的标点符号。所有的背景提示词（bg_prompt）必须严格使用英文关键词描述，严禁使用中文。
<br/>你的输出必须严格符合以下结构：<br/>
{
  "dialogue": "这是你说出的话，带有一点傲娇的语气",
  "mood": "必须包含表情与互动动作，例如 blushing, holding hands with player, angry, pointing finger at player, happy, leaning on player shoulder",
  "bg_prompt": "描述具体场景与氛围，如cafe, indoor, daylight 或 school roof, night, sunset"
}
"""
```

### PPRT创作
PPRT为前置提示词，应遵循Stable Diffusion提示词规则。示例如下：<br/>
```python
best quality, masterpiece, highres, 1girl, asuka langley, vibrant colors, anime style, soft lighting, sharp focus, looking at viewer, upper body,
```
需要注意的是，结尾应当有","。
<br/>
最后，若在本地完全部署本项目，则本项目适合拥有较好显卡的用户体验，最少应当拥有12G显存才能体验最低Modelfile和PPRT。<br/>
如果您有条件使用云端服务，将LLM模型配置在云端，那么，您在本地最低只需要4G显存就可以体验本项目！但前提是，您的显卡可以流畅运行Stable Diffusion文生图功能。
欢迎前往我们的Discord社区，那里有许多性能优化方案。欢迎您在Discord社区里做出贡献。本项目暂不支持PR，如果您想为本项目做出贡献，请在Discord社区联系我们。感谢您的支持！
