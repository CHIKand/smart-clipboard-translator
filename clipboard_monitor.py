"""后台剪贴板监听线程"""

import time
import threading
import hashlib

import pyperclip

from language_detector import contains_chinese
from translator import translate
from db import add_record, get_all_records


class ClipboardMonitor(threading.Thread):
    """后台剪贴板监听线程"""

    def __init__(self):
        super().__init__(daemon=True)
        self._running = False
        self._config = {}
        # 防死循环缓存
        self._last_original: str = ''
        self._last_translated: str = ''
        self._content_hash: str = ''
        # 回调
        self._on_translate_callback = None
        self._on_status_callback = None

    def set_config(self, config: dict) -> None:
        self._config = config

    def set_on_translate(self, callback) -> None:
        """翻译完成回调 (original, translated)"""
        self._on_translate_callback = callback

    def set_on_status(self, callback) -> None:
        """状态变化回调 (status: str)"""
        self._on_status_callback = callback

    def _notify_status(self, status: str) -> None:
        if self._on_status_callback:
            self._on_status_callback(status)

    def run(self) -> None:
        self._running = True
        self._notify_status('运行中')
        while self._running:
            try:
                current = pyperclip.paste()
            except Exception:
                time.sleep(self._config.get('poll_interval', 0.8))
                continue

            if not current or not isinstance(current, str):
                time.sleep(self._config.get('poll_interval', 0.8))
                continue

            # 防死循环：跳过上次翻译结果或原文
            if current.strip() == self._last_translated.strip():
                time.sleep(self._config.get('poll_interval', 0.8))
                continue
            if current.strip() == self._last_original.strip():
                time.sleep(self._config.get('poll_interval', 0.8))
                continue

            # 内容未变化则跳过
            current_hash = hashlib.md5(current.encode()).hexdigest()
            if current_hash == self._content_hash:
                time.sleep(self._config.get('poll_interval', 0.8))
                continue
            self._content_hash = current_hash

            # 只有包含中文才翻译
            if not contains_chinese(current):
                time.sleep(self._config.get('poll_interval', 0.8))
                continue

            # 获取前 1 条历史记录作为上下文
            try:
                history = get_all_records(limit=1)
            except Exception:
                history = []

            # 执行翻译
            self._notify_status('翻译中...')
            try:
                result = translate(current, self._config, history)
            except Exception as e:
                self._notify_status(f'翻译失败: {e}')
                time.sleep(self._config.get('poll_interval', 0.8))
                continue

            # 回写剪贴板
            self._last_original = current
            self._last_translated = result
            try:
                pyperclip.copy(result)
            except Exception:
                pass

            # 记录到数据库
            try:
                add_record(current, result)
            except Exception:
                pass

            # 通知 GUI 显示 toast
            if self._on_translate_callback:
                self._on_translate_callback(current, result)

            self._notify_status('运行中')
            time.sleep(self._config.get('poll_interval', 0.8))

    def stop(self) -> None:
        self._running = False
        self._notify_status('已停止')
