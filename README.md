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
<img width="439" height="470" alt="image" src="https://github.com/user-attachments/assets/aad33aec-9866-490a-961a-53e57fc42498" />

### 友好内容创作设计
使用Modelfile和PPRT自定义形式，允许你自己构建自己的林月！自定义说话方式、自定义外观易如反掌。你可以在我们的Discord社区获得别人制作好的成品。<br/>
<img width="751" height="418" alt="image" src="https://github.com/user-attachments/assets/f4cfc64e-86c4-4679-aeee-3019124e98d4" />

### 未来展望
目前支持自定义LLM模型。未来将支持自定义Stable Diffusion模型，实现进一步自定义。另外，我们在未来将加入语音自定义模块可供开关，优化对话体验。最重要的是，本项目开源且永远免费！本地部署是我们开发者的本钱。<br/>
<img width="1239" height="578" alt="image" src="https://github.com/user-attachments/assets/98e6728b-fea3-4af8-8890-59fa7189b038" />

## 使用教程
### 1.基本环境手动配置
安装Python3.11,以及Ollama最新版本。可搜索安装包一键安装，此处不赘述。<br/>
git拉取本仓库，创建文件夹models，并在下载模型anything-v5.safetensors存放在文件夹下。<a href="https://huggingface.co/genai-archive/anything-v5/tree/main">抱脸链接</a>
### 2.运行启动器检测并配置环境
使用python运行launcher.py<br/>
```bash
python launcher.py
```
<img width="442" height="466" alt="image" src="https://github.com/user-attachments/assets/336fe645-934f-41df-9bdb-3248ab2be070" />
<br/>接着启动器会检测环境并安装环境。如有报错，可截图发送到Discord社区进行求助。需要注意的是，此过程可能会安装一些AI大模型，这可能需要耗费很长的时间，请注意观察控制台。<br/>
配置成功后应如图所示，显示环境已就绪。
### 3.配置参数并启动
启动LinYue必须要有一个Modelfile，可选一个PPRT。这些都可以在Discord获得别人的成品。或者，你可以自行配置。首次启动一个Modelfile可能需要下载模型，请注意控制台。以及，游戏刚启动的第一句话初始化会很慢，请耐心等待。<br/>
渲染步数推荐在15-20左右，如果你的PPRT较为复杂，可选20-30步。但无论如何，渲染最少不能少于15步，否则将出现画面崩坏。<br/>
启动后即可开始游戏。如果需要清除记忆，点击清除按钮。如果你想保存记忆并重新开始一段记忆，可以将本地的galgame_save.json文件改名保存，再次启动游戏就会生成新的记忆文件。另外，每次更换Modelfile，我建议你都要重置一次记忆文件，无论是删除还是备份改名。否则，可能会出现意外结果。

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
最后，本项目适合拥有较好显卡的用户体验，最少应当拥有12G显存才能体验最低Modelfile和PPRT。<br/>
