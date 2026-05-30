# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

"智能剪贴板翻译器" — Windows 桌面应用，后台监听剪贴板，检测中文文本后通过大模型 API 翻译为英文并回写剪贴板。CustomTkinter 深色 GUI，SQLite 历史记录。

## 常用命令

```bash
# 运行应用
python main.py

# 安装依赖
pip install -r requirements.txt

# 打包为单个 exe（无控制台窗口）
pyinstaller --noconsole --onefile --name "智能剪贴板翻译器" \
  --hidden-import customtkinter --hidden-import win32clipboard \
  --hidden-import win32gui --hidden-import win32api main.py
```

## 架构

**核心线程模型**：GUI 在主线程（`App.mainloop()`），`ClipboardMonitor` 是独立 daemon 线程。Monitor 通过回调通知 GUI，GUI 用 `self.after(0, ...)` 将更新调度回主线程。

**配置存储**：`%APPDATA%/SmartClipboardTranslator/` 下两个文件：
- `config.json` — 当前配置 + `provider_configs`（按服务商隔离的 API 地址/Key/模型名）
- `profiles.json` — 用户保存的命名预设（一键切换整组配置）

切换内置预设时先保存当前字段到旧服务商的 `provider_configs` 槽位，再从新服务商加载。此逻辑在 `gui.py` 的 `_on_provider_changed()` 中，使用 `_last_provider_name` 追踪旧服务商名（因为 `_provider_var` 已被 OptionMenu 先更新）。

**翻译请求体组装**（`translator.py`）：`_build_payload()` 将 `system_prompt` + `custom_rules` 拼接为 system message，再 `json.loads(extra_params)` 合并到 payload 顶层（覆盖默认的 temperature/max_tokens）。v1.1.0 新增：插入最近 1 条翻译记录作为 user/assistant 消息对（few-shot 上下文），保证相似句型翻译风格一致。历史记录由 `clipboard_monitor.py` 调用前从 SQLite 获取。

**防死循环**（`clipboard_monitor.py`）：三层防护 — `_last_translated`（跳过刚写入的译文）、`_last_original`（跳过刚读取的原文）、`_content_hash`（内容未变不重复翻译）。只翻译含中文的文本（`language_detector.py`，Unicode `一-鿿` 范围）。

**GUI 配色**：`gui.py` 顶部 `COLORS` 字典定义全局色板，所有组件引用此字典。`_BaseDialog` 子类（`ProfileNameDialog`、`ConfirmDialog`）复刻主界面深色风格。

**Toast**（`toast.py`）：tkinter `Toplevel`，`overrideredirect(True)` 无边框，定位到 `win32gui.GetCursorPos()` 右下方，停留 400ms 后淡出约 400ms。

**打包注意事项**：必须 `--hidden-import` 指定 `customtkinter`、`win32clipboard`、`win32gui`、`win32api`，否则运行时找不到模块。
