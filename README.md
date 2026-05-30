# 智能剪贴板翻译器

Windows 桌面应用，后台监听剪贴板，检测中文文本后自动通过大模型 API 翻译为英文并回写剪贴板。

## 功能

- **后台剪贴板监听**：复制中文文本后自动翻译为英文，直接粘贴即可使用
- **多厂商支持**：内置 DeepSeek / 通义千问 / 智谱 GLM / Kimi / 豆包 / 零一万物预设
- **翻译上下文记忆**：自动将最近 1 次翻译结果作为 few-shot 示例发送，保证相似句型翻译风格一致
- **个人翻译偏好**：可自定义翻译规则（术语映射、风格要求等），自动注入系统提示词
- **历史记录**：SQLite 本地存储，支持搜索和删除
- **配置预设**：一键保存/切换多套 API 配置

## 安装

下载 [最新 Release](https://github.com/CHIKand/smart-clipboard-translator/releases) 中的 `智能剪贴板翻译器.exe`，双击运行即可。

## 自行打包

```bash
pip install -r requirements.txt
pyinstaller --noconsole --onefile --name "智能剪贴板翻译器" \
  --hidden-import customtkinter --hidden-import win32clipboard \
  --hidden-import win32gui --hidden-import win32api main.py
```

## 技术栈

Python 3.9+ / CustomTkinter / SQLite / OpenAI 兼容 API
