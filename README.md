# LinYue AiChat Game
林月，基于Stable Diffusion以及LLM实现的本地AI生成ACG游戏，拥有启动器指引进行部署，上手难度较低。<br/>
本项目的README文件是极为简单的配置教程。需要更进一步体验LinYue，请移步Discord社区。
<a href="https://discord.gg/VseVN2aRBf">我们的Discord社区</a> 
<a href="https://qun.qq.com/universal-share/share?ac=1&svctype=5&tempid=h5_group_info&busi_data=eyJncm91cENvZGUiOiIxMDM4MzY4NDA4In0%3D" target="_blank">加入QQ群1038368408</a>
## 特色
### 内容完全由Ai生成
内容完全由Ai生成，你输入的文本，被Ai响应后生成文本和图片，一切都是未知的。<br/>
<img width="1263" height="711" alt="image" src="https://github.com/user-attachments/assets/3fd0f1ff-00ff-4b79-b274-3f58c2b45ad9" />


### Ai状态栏
<img width="320" height="204" alt="image" src="https://github.com/user-attachments/assets/e9ac8d0a-9d95-4938-9fe6-19dcd24d1d8b" />

### 长记忆储存
算法优化，定期总结，经测试实现了150轮对话记忆不缺失！<br/>
<img width="1273" height="712" alt="image" src="https://github.com/user-attachments/assets/dbc0fb57-4d55-4794-89d9-349631d45aa8" />

### 智能转场
转场不归游戏代码管，归Ai和你来管！智能检测当前正在做的事件，允许玩家手动跳过，Ai觉得无聊或者事情太长，也会自己跳过哦！<br/>
<img width="787" height="104" alt="image" src="https://github.com/user-attachments/assets/5eabf7fa-0c8a-4a38-85c5-6b4a732cb01b" />

### 历史记录随心查看
忘记之前说什么了，可以回到历史记录去找。所有生成过的图片和文本都会被储存起来，以备不时之需。<br/>
<img width="1250" height="710" alt="image" src="https://github.com/user-attachments/assets/cac916e8-9d7f-4bfe-8cad-49f42c715bc6" />


### 启动器设计
拥有启动器设计，智能检测和配置环境，允许一键设置参数。方便快捷。<br/>
<img width="466" height="788" alt="image" src="https://github.com/user-attachments/assets/f10d3e65-4b85-4dfd-9417-f961e94f09cc" />


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

---

## 使用教程（新）
### 简介
欢迎您选择游玩LinYue AiChat Game. 本游戏由Python编写，使用LLM大模型和Stable Diffusion为后端，是新生代Ai ACG游戏。<br/>
本游戏上手游玩需要有一定的计算机基础和稍高的计算机配置，请您务必注意。最重要的是，一定要有科学上网。<br/>
若有疑问，可前往QQ群或Discord社区询问。<br/>
### 服务端
本游戏本体分为客户端和服务端。本部分教程将先指导您配置游戏服务端。配置好服务端后，您可以分享地址给他人，他人一样可以使用您配置好的服务端。同样的，您可以使用他人已经配置好的服务端来跳过这一步骤。<br/>
**1、基本须知**<br/>
服务端只需要一个文件就可以启动，但不代表它不需要环境。服务器启动的必需品有三个：配置完全的python环境 + 配置好的ollama + 可以使用的modelfile<br/>
*Modelfile: 指导LLM模型语言的文件，作用于Ollama，具有固定的格式。详情请翻阅底部创作者指南。您可以在Discord或网络上下载制作好的modelfile。* <br/>
*python环境需求：python3.11.x + 安装过目录下requirements.txt* <br/>
*ollama: 最新版本ollama即可，一键安装后可直接使用。* <br/>
<a href="https://ollama.com/download">Ollama</a> <a href="https://www.python.org/downloads/release/python-3110/">Python 3.11</a><br/>
**2、安装并启动**<br/>
安装好Ollama和python后，在server目录下按住shift+右键，打开powershell。或者您可以使用win + r快捷键，接着输入cmd打开命令提示符，使用cd命令切换到当前目录。<br/>
<img width="257" height="79" alt="image" src="https://github.com/user-attachments/assets/7552ef00-5cd8-4f17-b804-428d0c376ca5" />
在当前目录下输入命令：<br/>
```bash
pip install -r requirements.txt
```
安装成功后，输入python server.py -h可查看服务端参数介绍。<br/>
<img width="1047" height="263" alt="image" src="https://github.com/user-attachments/assets/90953bdd-bcb7-4490-909e-e001ce44c302" />
如无特别需要，下面的命令即可使用：<br/>
```bash
python server --new-api
python server.py -p 17775 -modelfile [你的modelfile] 
```
第一个命令获取了5个APIKEY，请复制其中一个用于您的客户端。这些apikey会保存在文件夹下。启动成功后则可以将窗口切至后台。*但千万不能关闭！* <br/>
### 客户端
本游戏的客户端启动非常简单，因为我们直接使用启动器启动， 它会帮助你配置依赖项。<br/>
**1. 下载模型** <br/>
在启动器启动器前，您需要通过科学上网或者其他方式，下载一个模型。<a href="https://huggingface.co/genai-archive/anything-v5/tree/main">抱脸链接</a><br/>
请下载其中的anything-v5.safetensors，并保存在models文件夹下。目前不建议使用其他模型，可能会出现意料之外的错误。（截止2026.6.30更新）
**2. 启动启动器** <br/>
切换到客户端根目录，输入以下命令：<br/>
```bash
python launcher.py
```
无需任何参数，即可启动启动器。启动器启动后，会第一时间配置环境。您可以在终端看到配置情况，如果有报错，请截图求助。<br/>
<img width="468" height="794" alt="image" src="https://github.com/user-attachments/assets/8cf0d055-b701-4236-a070-ea44260918c1" /><br/>
成功启动后您可以看见如上图所示的窗口。还记得刚才需要您记住的Apikey吗？请输入它。请务必记住，在服务器地址这一栏上输入你的服务器IP+你刚才设置的-p端口。（如果您是本地部署，ip为127.0.0.1）接着，可以根据需要配置好您的参数。随即点击下方启动按钮即可启动游戏！<br/>
*关于Modelfile: 配置AI语言规范的文件，在客户端不作用于Ollama，而是交给游戏解析。若您的服务器应用了一个含有人格描述内容/剧情设计等详细内容的modelfile，那么我建议您在本地不要再使用modelfile，否则会引起奇怪的效果。如果您的服务器使用的是空白modelfile（modelfile文件中的system提示词只有语言规范，没有个性设计等内容），那么您本地请务必使用一个您喜欢的modelfile。* <br/>
*关于pprt：配置ai作图的提示词。您可以在最后的创作者指南中找到配置方法。您可以下载别人配置好的pprt使用。* <br/>
*关于低显存模式：显存低于16G，均需要开启低显存模式。16G及以上可选择关闭此模式，可以大大加快响应速度。* <br/>
*关于记忆总结：推荐开启，除非您使用了超长上下文的模型以及拥有一块超大显存的显卡。建议设置在12-18轮开启总结。* <br/>
*关于渲染步数：目前引擎采用DPM++采样方法，推荐使用15-20步取得最佳效果。* <br/>
*关于存档：您每次游戏，都会不停自动保存存档。如果您切换了modelfile，建议您重置存档。如果您想保存/切换存档，可自行替换目录下的galgame_save.json。* <br/>
## 使用教程（旧）
（下方为旧版本教程 可跳过 直接查看上面的新版教程）
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
(旧版本)<br/>
<img width="417" height="410" alt="image" src="https://github.com/user-attachments/assets/e32d99f5-6815-407a-8706-ebd856d43c87" />
(新版本)<br/>
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
如果你的电脑配置低，显存不足，只允许运行Stable Diffusion的话，使用云端服务器是最好的解决方案！你可以购买付费的小时计云GPU服务器来配置并保存镜像，这是一种可行方案。或者，去我们的Discord社区转转，那里可能有免费的公益服务器。<br/>
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
最后，若在本地完全部署本项目，则本项目适合拥有较好显卡的用户体验，最少应当拥有10G显存才能体验最低Modelfile和PPRT。<br/>
如果您有条件使用云端服务，将LLM模型配置在云端，那么，您在本地最低只需要4G显存就可以体验本项目！但前提是，您的显卡可以流畅运行Stable Diffusion文生图功能。
欢迎前往我们的Discord社区，那里有许多性能优化方案。欢迎您在Discord社区里做出贡献。本项目暂不支持PR，如果您想为本项目做出贡献，请在Discord社区联系我们。感谢您的支持！
