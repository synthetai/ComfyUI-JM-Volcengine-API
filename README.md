# ComfyUI Volcengine SeeDream V3 Node

这是一个用于ComfyUI的自定义节点，可以调用火山引擎通用3.0文生图模型API来生成图像。

## 功能特性

- 调用火山引擎SeeDream V3文生图API
- 支持所有官方API参数
- 自动处理API签名验证
- 支持URL和Base64图像响应格式
- 完整的错误处理机制
- 同时输出图像和图片URL链接
- 自动保存图片到本地文件，支持自定义文件名前缀

## 安装

1. 将此项目克隆到ComfyUI的custom_nodes目录下：
```bash
cd ComfyUI/custom_nodes/
git clone [your-repo-url] ComfyUI-JM-Volcengine-API
```

2. 安装依赖：
```bash
cd ComfyUI-JM-Volcengine-API
pip install -r requirements.txt
```

3. 重启ComfyUI

## 使用方法

### 节点参数

#### 输出参数
- **image**: 生成的图像（IMAGE格式）
- **image_url**: 图片下载链接（STRING格式，24小时有效）

#### 必需参数
- **access_key**: 火山引擎API访问密钥
- **secret_key**: 火山引擎API秘钥
- **prompt**: 图像生成提示词（支持中英文）

#### 可选参数
- **use_pre_llm**: 是否开启文本扩写（默认：False）
- **seed**: 随机种子，用于生成可重复的结果（默认：-1为随机）
- **guidance_scale**: 文本描述的影响程度（默认：2.5，范围：1.0-10.0）
- **aspect_ratio**: 图像宽高比，支持1.5K分辨率预设（默认：1:1）
- **return_url**: 是否返回图片URL链接（默认：True）
- **filename_prefix**: 本地保存文件名前缀（默认：seedream）

### 支持的图像分辨率 (1.5K)

节点支持以下预设的1.5K分辨率比例选项：
- **1:1** → 1536×1536 (正方形)
- **4:3** → 1472×1104 (传统照片比例)
- **3:2** → 1584×1056 (经典摄影比例)
- **16:9** → 1664×936 (宽屏比例)
- **9:16** → 936×1664 (竖屏比例，适合手机wallpaper)
- **21:9** → 2016×864 (超宽屏比例)

### 提示词优化技巧

1. **画面描述**: 使用连贯的自然语言描述画面内容（主体+行为+环境等）
2. **美学描述**: 用短词语描述画面美学（风格、色彩、光影、构图等）
3. **专业词汇**: 推荐使用英文描述专业词汇，获得更精准效果
4. **图像用途**: 说明图像用途和类型，如"PPT封面背景图"、"广告海报设计"等
5. **文字排版**: 将文字内容置于双引号""内，并描述文字的大小、字体、颜色、风格和位置

### 示例提示词

```
【风格：漫画风格】【镜头视角：特写】一个可爱的机器人在花园里浇花，阳光明媚，色彩鲜艳，卡通风格
```

### 参数说明对照表

| 节点参数名 | API参数名 | 说明 |
|-----------|-----------|------|
| access_key | - | 火山引擎API访问密钥 |
| secret_key | - | 火山引擎API密钥 |
| prompt | prompt | 图像生成提示词 |
| use_pre_llm | use_pre_llm | 文本扩写增强 |
| seed | seed | 随机种子 |
| guidance_scale | scale | 引导强度 |
| aspect_ratio | width/height | 自动设置宽高比 |
| return_url | return_url | 返回图片URL |
| filename_prefix | - | 本地文件名前缀 |

## 节点位置

在ComfyUI中，您可以在以下位置找到该节点：
**Add Node → JM-Volcengine-API/Seedream → volcengine-seedream-v3**

## API配置

1. 登录火山引擎控制台
2. 获取您的access_key和secret_key
3. 确保您的账户有足够的API调用额度

## 错误处理

节点包含完整的错误处理机制：
- API密钥验证
- 网络请求超时处理
- 图像下载失败处理
- API响应错误处理

如果生成失败，节点会返回一个空白图像并在控制台输出错误信息。

## 注意事项

- 图像链接有效期为24小时
- 建议使用1.3K-1.5K分辨率获得最佳画质
- 请合理使用API避免超出配额限制
- 网络环境需要能够访问火山引擎API服务
- image_url输出可以用于后续的图像处理或保存链接
- 生成的图片会自动保存到`output`目录下，文件名格式为`{filename_prefix}_0001.png`
- 如果文件名重复，序号会自动递增（如：`seedream_0002.png`）

## 技术支持

如果您遇到任何问题，请检查：
1. API密钥是否正确
2. 网络连接是否正常
3. ComfyUI控制台的错误信息
4. 火山引擎API配额是否充足

## 许可证

本项目基于MIT许可证开源。 