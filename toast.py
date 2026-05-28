"""光标处提示弹窗"""

import tkinter as tk
import win32gui
import win32api


class Toast:
    """翻译完成提示弹窗"""

    def __init__(self, parent: tk.Tk):
        self._parent = parent
        self._window: tk.Toplevel | None = None
        self._after_id = None

    def show(self, message: str = '翻译完成，可以粘贴', success: bool = True) -> None:
        """在鼠标光标位置显示提示"""
        if self._window is not None:
            try:
                self._window.destroy()
            except tk.TclError:
                pass

        x, y = win32gui.GetCursorPos()

        self._window = tk.Toplevel(self._parent)
        self._window.overrideredirect(True)
        self._window.attributes('-topmost', True)

        frame = tk.Frame(
            self._window, bg='#1a1e27',
            highlightbackground='#252a35', highlightthickness=1, bd=0,
        )
        frame.pack()

        inner = tk.Frame(frame, bg='#1a1e27', bd=0)
        inner.pack(padx=16, pady=12)

        color = '#22c55e' if success else '#ef4444'
        symbol = '✓' if success else '✗'
        check = tk.Label(
            inner, text=symbol, fg=color, bg='#1a1e27',
            font=('Microsoft YaHei', 13, 'bold'),
        )
        check.pack(side=tk.LEFT, padx=(0, 10))

        label = tk.Label(
            inner, text=message, fg='#e4e7ef', bg='#1a1e27',
            font=('Microsoft YaHei', 11),
        )
        label.pack(side=tk.LEFT)

        self._window.geometry(f'+{x + 12}+{y + 16}')
        try:
            self._window.attributes('-alpha', 0.95)
        except tk.TclError:
            pass

        # 停留 400ms 后开始淡出（总约 0.8 秒）
        self._after_id = self._window.after(400, self._fade_out)

    def _fade_out(self) -> None:
        if self._window is None:
            return
        try:
            current = self._window.attributes('-alpha')
            if current <= 0.05:
                self._window.destroy()
                self._window = None
                return
            self._window.attributes('-alpha', current - 0.10)
            self._after_id = self._window.after(40, self._fade_out)
        except tk.TclError:
            self._window = None
