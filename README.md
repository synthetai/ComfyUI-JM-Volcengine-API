# ComfyUI 火山引擎 API 插件

这是一个为 ComfyUI 开发的火山引擎AI服务插件，支持多种火山引擎API功能。

## 功能特性

### 1. Volcengine SeeDream V3 - 文生图节点
- 火山引擎即梦AI SeeDream V3 文生图模型
- 支持1.5K分辨率图片生成
- 支持多种宽高比：1:1、4:3、3:2、16:9、9:16、21:9
- 自动保存生成的图片到输出目录
- 同时返回图片URL和本地文件路径

### 2. Volcengine I2V S2.0Pro - 图生视频节点 (新增)
- 火山引擎即梦AI图生视频S2.0Pro专业级模型
- 从静态图片生成高质量动态视频
- 支持多种视频宽高比：16:9、4:3、1:1、3:4、9:16、21:9、9:21
- 支持中英文提示词，最大150字符
- 异步处理，自动轮询查询结果
- 视频时长固定5秒
- 自动下载和保存视频文件

## 安装

1. 克隆此仓库到 ComfyUI 的 custom_nodes 目录：
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/your-repo/ComfyUI-JM-Volcengine-API.git
```

2. 安装依赖：
```bash
cd ComfyUI-JM-Volcengine-API
pip install -r requirements.txt
```

3. 重启 ComfyUI

## 使用方法

### Volcengine SeeDream V3 使用
1. 在节点列表中找到 `JM-Volcengine-API/Seedream` 分类
2. 添加 `Volcengine SeeDream V3` 节点
3. 配置参数：
   - **access_key**: 火山引擎访问密钥
   - **secret_key**: 火山引擎访问密钥
   - **prompt**: 图片生成提示词
   - **aspect_ratio**: 选择宽高比
   - **guidance_scale**: 引导强度 (可选)
   - **seed**: 随机种子 (可选)
   - **use_pre_llm**: 是否使用预处理LLM (可选)
   - **filename_prefix**: 保存文件名前缀 (可选)

### Volcengine I2V S2.0Pro 使用 (新增功能)
1. 在节点列表中找到 `JM-Volcengine-API/I2V` 分类
2. 添加 `Volcengine I2V S2.0Pro` 节点
3. 配置参数：
   - **access_key**: 火山引擎访问密钥AccessKey
   - **secret_key**: 火山引擎访问密钥SecretKey
   - **image**: 输入图片 (连接图片节点)
   - **aspect_ratio**: 选择视频宽高比
   - **prompt**: 视频生成提示词 (可选，最大150字符)
   - **seed**: 随机种子 (可选，-1表示随机)
   - **filename_prefix**: 保存文件名前缀 (可选)

## 参数说明

### SeeDream V3 参数
- **宽高比选项**：
  - 1:1 → 1536×1536
  - 4:3 → 1472×1104
  - 3:2 → 1584×1056
  - 16:9 → 1664×936
  - 9:16 → 936×1664
  - 21:9 → 2016×864

- **guidance_scale**: 1.0-20.0，控制生成图片与提示词的匹配程度
- **use_pre_llm**: 是否使用预处理大语言模型优化提示词

### I2V S2.0Pro 参数 (新增)
- **支持的宽高比**：
  - 16:9 → 适合横向视频
  - 4:3 → 传统电视比例
  - 1:1 → 正方形视频
  - 3:4 → 竖向视频
  - 9:16 → 手机竖屏视频
  - 21:9 → 超宽屏视频
  - 9:21 → 超高竖屏视频

- **提示词优化建议**：
  - 与输入图片内容保持一致
  - 描述期望的动作和运镜效果
  - 支持中英文，建议使用简洁明确的描述
  - 可以包含镜头切换、人物动作、情绪演绎等描述

## 输出说明

### SeeDream V3 输出
- **image**: 生成的图片张量，可连接到其他节点
- **image_url**: 图片的临时URL链接
- **local_image_path**: 本地保存的图片文件路径

### I2V S2.0Pro 输出 (新增)
- **video_url**: 生成的视频URL链接 (有效期1小时)
- **local_video_path**: 本地保存的视频文件路径

## 注意事项

### 通用注意事项
1. 需要有效的火山引擎访问密钥
2. 网络连接需要稳定
3. 生成的内容需要符合平台规范

### SeeDream V3 特定注意事项
- 图片生成为同步处理，通常几秒内完成
- 生成的图片会自动保存到ComfyUI的output目录
- 临时URL链接有效期较短，建议及时保存

### I2V S2.0Pro 特定注意事项 (新增)
- 视频生成为异步处理，通常需要几分钟时间
- 程序会自动轮询查询结果，请耐心等待
- 生成的视频时长固定为5秒
- 视频URL有效期为1小时，请及时下载保存
- 输入图片和提示词需要通过内容审核
- 建议根据输入图片的实际比例选择合适的aspect_ratio

## 错误处理

### 常见错误及解决方案

#### SeeDream V3
- **认证失败**: 检查access_key和secret_key是否正确
- **参数错误**: 确认提示词长度和参数范围
- **网络错误**: 检查网络连接状态

#### I2V S2.0Pro (新增)
- **认证失败**: 检查AccessKey和SecretKey是否正确并有相应权限
- **图片审核未通过**: 检查输入图片内容是否符合平台规范
- **文本审核未通过**: 检查提示词内容是否合规
- **任务超时**: 可能服务器繁忙，可稍后重试
- **宽高比不匹配**: 建议选择与输入图片比例接近的aspect_ratio

## 技术实现

### SeeDream V3
- 使用火山引擎AWS V4签名算法进行认证
- 支持URL和Base64两种图片返回格式
- 自动处理ComfyUI张量格式转换

### I2V S2.0Pro (新增)
- 实现火山引擎标准签名V4算法
- 异步任务处理机制，支持轮询查询
- 图片自动转换为Base64格式上传
- 完整的错误处理和重试机制
- 视频文件自动下载和命名管理

## 系统要求
- ComfyUI 环境
- Python 3.8+
- 稳定的网络连接
- 有效的火山引擎API访问权限

## 更新日志

### v2.0.0 (最新)
- 新增 Volcengine I2V S2.0Pro 图生视频节点
- 支持从图片生成高质量5秒视频
- 支持7种视频宽高比选择
- 实现异步任务处理和自动轮询
- 添加完整的火山引擎签名认证
- 支持视频自动下载和保存

### v1.0.0
- 初始版本
- 支持 Volcengine SeeDream V3 文生图功能
- 支持1.5K分辨率和多种宽高比
- 实现AWS V4签名认证
- 支持图片自动保存和URL返回

## 技术支持

如有问题或建议，请提交Issue或Pull Request。

## 许可证

本项目采用 MIT 许可证。 