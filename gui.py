"""主界面 - CustomTkinter 实现"""

import threading
import customtkinter as ctk

from config_manager import (
    load_config, save_config, switch_provider,
    PRESET_PROVIDERS, load_profiles, save_profile, delete_profile,
)
from db import get_all_records, search_records, delete_record, get_record_count
from translator import test_connection
from clipboard_monitor import ClipboardMonitor
from toast import Toast

# ---- 配色方案 ----
COLORS = {
    'bg_root': '#0b0d10',
    'bg_surface': '#13161c',
    'bg_card': '#1a1e27',
    'bg_input': '#11141b',
    'border': '#252a35',
    'border_focus': '#3b4458',
    'text_primary': '#e4e7ef',
    'text_secondary': '#8b919f',
    'text_muted': '#5c6270',
    'accent_green': '#22c55e',
    'accent_green_dim': '#166534',
    'accent_red': '#ef4444',
    'accent_red_dim': '#7f1d1d',
    'accent_blue': '#60a5fa',
    'accent_blue_dim': '#1e3a5f',
}


def _section_label(parent, text: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        parent, text=text, anchor='w',
        font=('Microsoft YaHei', 10, 'bold'),
        text_color=COLORS['text_secondary'],
    )


def _make_entry(parent, var, placeholder='', show='') -> ctk.CTkEntry:
    return ctk.CTkEntry(
        parent, textvariable=var, placeholder_text=placeholder, show=show,
        fg_color=COLORS['bg_input'], border_color=COLORS['border'],
        text_color=COLORS['text_primary'],
        font=('Microsoft YaHei', 12), height=36,
    )


def _make_textbox(parent, height=60) -> ctk.CTkTextbox:
    return ctk.CTkTextbox(
        parent,
        fg_color=COLORS['bg_input'], border_color=COLORS['border'],
        text_color=COLORS['text_primary'],
        font=('Microsoft YaHei', 11), height=height,
    )


def _build_provider_values() -> list[str]:
    """构建预设下拉菜单项"""
    builtin = list(PRESET_PROVIDERS.keys())
    profiles = load_profiles()
    if profiles:
        return builtin + ['───── 我的预设 ─────'] + list(profiles.keys())
    return builtin


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.title('智能剪贴板翻译器')
        self.geometry('480x620')
        self.resizable(False, False)
        ctk.set_appearance_mode('dark')
        self.configure(fg_color=COLORS['bg_surface'])

        self._monitor = ClipboardMonitor()
        self._monitor.set_config(self.config_data)
        self._monitor.set_on_translate(self._on_translate_done)
        self._monitor.set_on_status(self._on_status_change)
        self._toast = Toast(self)
        self._advanced_open = False
        self._auto_save_enabled = False
        self._last_provider_name = self.config_data.get('api_provider', 'DeepSeek')

        self._build_ui()
        self._load_config_to_ui()
        self._auto_save_enabled = True

    def _build_ui(self) -> None:
        self._build_title_bar()
        self._scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color='transparent',
            scrollbar_fg_color=COLORS['bg_card'],
            scrollbar_button_color=COLORS['border'],
            scrollbar_button_hover_color=COLORS['border_focus'],
        )
        self._scroll_frame.pack(fill='both', expand=True, padx=2, pady=0)
        self._build_main_fields()
        self._build_action_button()
        self._build_advanced_toggle()
        self._build_advanced_panel()
        self._build_bottom_bar()
        self._build_footer()

    # ======== 标题栏 ========
    def _build_title_bar(self) -> None:
        bar = ctk.CTkFrame(
            self, fg_color=COLORS['bg_card'], height=48, corner_radius=0,
        )
        bar.pack(fill='x', padx=0, pady=(0, 1))
        bar.pack_propagate(False)

        left = ctk.CTkFrame(bar, fg_color='transparent')
        left.pack(side='left', padx=(16, 0), pady=10)
        ctk.CTkLabel(
            left, text='📋', font=('Segoe UI Emoji', 16),
        ).pack(side='left', padx=(0, 8))
        ctk.CTkLabel(
            left, text='智能剪贴板翻译器',
            font=('Microsoft YaHei', 13, 'bold'),
            text_color=COLORS['text_primary'],
        ).pack(side='left')

        right = ctk.CTkFrame(bar, fg_color='transparent')
        right.pack(side='right', padx=(0, 16), pady=10)
        self._status_dot = ctk.CTkLabel(
            right, text='●', font=('Segoe UI Emoji', 10),
            text_color=COLORS['accent_red'],
        )
        self._status_dot.pack(side='left', padx=(0, 5))
        self._status_label = ctk.CTkLabel(
            right, text='已停止',
            font=('Microsoft YaHei', 10),
            text_color=COLORS['text_secondary'],
        )
        self._status_label.pack(side='left')

    # ======== 主输入区 ========
    def _build_main_fields(self) -> None:
        fields = ctk.CTkFrame(self._scroll_frame, fg_color='transparent')
        fields.pack(fill='x', padx=18, pady=(16, 8))

        # 配置预设
        _section_label(fields, '配置预设').pack(anchor='w', pady=(0, 4))

        provider_row = ctk.CTkFrame(fields, fg_color='transparent')
        provider_row.pack(fill='x', pady=(0, 10))

        self._provider_var = ctk.StringVar(value='DeepSeek')
        values = _build_provider_values()
        self._provider_menu = ctk.CTkOptionMenu(
            provider_row, values=values, variable=self._provider_var,
            fg_color=COLORS['bg_input'], button_color=COLORS['accent_blue_dim'],
            button_hover_color='#2a4a7a', text_color=COLORS['text_primary'],
            font=('Microsoft YaHei', 12), height=36,
            command=self._on_provider_changed,
        )
        self._provider_menu.pack(side='left', fill='x', expand=True)

        # 删除预设按钮（默认隐藏）
        self._del_profile_btn = ctk.CTkButton(
            provider_row, text='🗑', width=36, height=36,
            fg_color='transparent', hover_color='#4a1515',
            font=('Segoe UI Emoji', 14),
            command=self._delete_profile,
        )

        # API 地址
        _section_label(fields, 'API 地址').pack(anchor='w', pady=(0, 4))
        self._api_url_var = ctk.StringVar()
        self._api_url_var.trace('w', lambda *a: self._auto_save())
        _make_entry(fields, self._api_url_var, 'https://api.example.com/v1/chat/completions').pack(
            fill='x', pady=(0, 10),
        )

        # API Key
        _section_label(fields, 'API Key').pack(anchor='w', pady=(0, 4))
        key_frame = ctk.CTkFrame(fields, fg_color='transparent')
        key_frame.pack(fill='x', pady=(0, 10))
        self._api_key_var = ctk.StringVar()
        self._api_key_var.trace('w', lambda *a: self._auto_save())
        self._api_key_entry = _make_entry(key_frame, self._api_key_var, '输入你的 API Key', show='•')
        self._api_key_entry.pack(side='left', fill='x', expand=True)
        self._eye_btn = ctk.CTkButton(
            key_frame, text='👁', width=36, height=36,
            fg_color='transparent', hover_color='#252a35',
            font=('Segoe UI Emoji', 14),
            command=self._toggle_key_visibility,
        )
        self._eye_btn.pack(side='right', padx=(4, 0))

        # 模型名称
        _section_label(fields, '模型名称').pack(anchor='w', pady=(0, 4))
        self._model_name_var = ctk.StringVar()
        self._model_name_var.trace('w', lambda *a: self._auto_save())
        _make_entry(fields, self._model_name_var, '例如: deepseek-chat').pack(fill='x')

    def _refresh_provider_menu(self) -> None:
        """原地更新下拉菜单项（不重建 widget）"""
        values = _build_provider_values()
        self._provider_menu.configure(values=values)

    def _update_delete_btn_visibility(self) -> None:
        """根据当前选中项显示/隐藏删除按钮"""
        choice = self._provider_var.get()
        profiles = load_profiles()
        if choice in profiles:
            self._del_profile_btn.pack(side='right', padx=(4, 0))
        else:
            self._del_profile_btn.pack_forget()

    # ======== 启动/停止按钮 ========
    def _build_action_button(self) -> None:
        btn_frame = ctk.CTkFrame(self._scroll_frame, fg_color='transparent')
        btn_frame.pack(fill='x', padx=18, pady=(14, 4))
        self._toggle_btn = ctk.CTkButton(
            btn_frame, text='▶  启动监听',
            command=self._toggle_monitoring,
            fg_color=COLORS['accent_green_dim'],
            hover_color='#1a7a37',
            text_color='#bbf7d0',
            font=('Microsoft YaHei', 14, 'bold'),
            height=46, corner_radius=10,
        )
        self._toggle_btn.pack(fill='x')

    # ======== 高级参数折叠按钮 ========
    def _build_advanced_toggle(self) -> None:
        toggle_frame = ctk.CTkFrame(self._scroll_frame, fg_color='transparent')
        toggle_frame.pack(fill='x', padx=18, pady=(6, 0))
        self._adv_btn = ctk.CTkButton(
            toggle_frame, text='高级参数  ▸',
            command=self._toggle_advanced,
            fg_color='transparent', hover_color='#1e2430',
            text_color=COLORS['text_muted'],
            font=('Microsoft YaHei', 11), height=28,
        )
        self._adv_btn.pack(fill='x')

    # ======== 高级参数面板 ========
    def _build_advanced_panel(self) -> None:
        self._adv_panel = ctk.CTkFrame(
            self._scroll_frame, fg_color=COLORS['bg_card'],
            border_color=COLORS['border'], border_width=1,
            corner_radius=10,
        )
        inner = ctk.CTkFrame(self._adv_panel, fg_color='transparent')
        inner.pack(fill='x', padx=14, pady=(14, 6))

        # Temperature
        _section_label(inner, 'Temperature').pack(anchor='w', pady=(0, 4))
        temp_row = ctk.CTkFrame(inner, fg_color='transparent')
        temp_row.pack(fill='x', pady=(0, 10))
        self._temp_var = ctk.DoubleVar(value=0.3)
        self._temp_var.trace('w', lambda *a: self._auto_save())
        self._temp_slider = ctk.CTkSlider(
            temp_row, from_=0, to=2, number_of_steps=20,
            variable=self._temp_var, command=self._on_temp_changed,
            fg_color=COLORS['border'], progress_color=COLORS['accent_blue'],
            button_color=COLORS['accent_blue'],
            button_hover_color='#93c5fd',
        )
        self._temp_slider.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self._temp_value_label = ctk.CTkLabel(
            temp_row, text='0.3', width=38, height=24,
            font=('Consolas', 12, 'bold'),
            text_color=COLORS['accent_blue'],
            fg_color=COLORS['accent_blue_dim'],
            corner_radius=4,
        )
        self._temp_value_label.pack(side='right')

        # Max Tokens
        _section_label(inner, 'Max Tokens').pack(anchor='w', pady=(0, 4))
        self._max_tokens_var = ctk.StringVar(value='2000')
        self._max_tokens_var.trace('w', lambda *a: self._auto_save())
        _make_entry(inner, self._max_tokens_var).pack(fill='x', pady=(0, 10))

        # System Prompt
        _section_label(inner, 'System Prompt').pack(anchor='w', pady=(0, 4))
        self._system_prompt_text = _make_textbox(inner)
        self._system_prompt_text.bind('<FocusOut>', lambda e: self._auto_save())
        self._system_prompt_text.bind('<KeyRelease>', lambda e: self._auto_save())
        self._system_prompt_text.pack(fill='x', pady=(0, 10))

        # 个人翻译偏好
        _section_label(inner, '个人翻译偏好').pack(anchor='w', pady=(0, 4))
        self._custom_rules_text = _make_textbox(inner)
        self._custom_rules_text.bind('<FocusOut>', lambda e: self._auto_save())
        self._custom_rules_text.bind('<KeyRelease>', lambda e: self._auto_save())
        self._custom_rules_text.pack(fill='x', pady=(0, 10))

        # 请求参数覆盖 (JSON)
        _section_label(inner, '请求参数覆盖 (JSON)').pack(anchor='w', pady=(0, 4))
        ctk.CTkLabel(
            inner,
            text='可覆盖任意 API 请求体字段，如 {"top_p": 0.9}，留空则使用默认值',
            font=('Microsoft YaHei', 9), text_color=COLORS['text_muted'], anchor='w',
        ).pack(fill='x', pady=(0, 4))
        self._extra_params_text = _make_textbox(inner, height=80)
        self._extra_params_text.bind('<FocusOut>', lambda e: self._auto_save())
        self._extra_params_text.bind('<KeyRelease>', lambda e: self._auto_save())
        self._extra_params_text.pack(fill='x', pady=(0, 10))

        # 轮询间隔
        _section_label(inner, '轮询间隔（秒）').pack(anchor='w', pady=(0, 4))
        self._poll_interval_var = ctk.StringVar(value='0.8')
        self._poll_interval_var.trace('w', lambda *a: self._auto_save())
        _make_entry(inner, self._poll_interval_var).pack(fill='x')

    # ======== 底部按钮栏 ========
    def _build_bottom_bar(self) -> None:
        bar = ctk.CTkFrame(self._scroll_frame, fg_color='transparent')
        bar.pack(fill='x', padx=18, pady=(14, 10))

        self._history_btn = ctk.CTkButton(
            bar, text='📄 历史记录', command=self._open_history,
            fg_color=COLORS['bg_card'], hover_color='#252d38',
            text_color=COLORS['text_secondary'],
            border_color=COLORS['border'], border_width=1,
            font=('Microsoft YaHei', 12), height=34, corner_radius=8,
        )
        self._history_btn.pack(side='left', fill='x', expand=True, padx=(0, 5))

        self._save_btn = ctk.CTkButton(
            bar, text='💾 保存为预设', command=self._save_as_profile,
            fg_color=COLORS['accent_blue_dim'], hover_color='#2a4a7a',
            text_color=COLORS['accent_blue'],
            border_color='#3a6aaa', border_width=1,
            font=('Microsoft YaHei', 12), height=34, corner_radius=8,
        )
        self._save_btn.pack(side='right', fill='x', expand=True, padx=(5, 0))

    # ======== 底部版本号 ========
    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color='transparent')
        footer.pack(fill='x', side='bottom')
        ctk.CTkLabel(
            footer, text='智能剪贴板翻译器 v1.1.0',
            font=('Microsoft YaHei', 9),
            text_color=COLORS['text_muted'],
        ).pack(pady=(2, 6))

    # ======== 自动保存 ========
    def _auto_save(self) -> None:
        if not self._auto_save_enabled:
            return
        self._apply_ui_to_config()
        save_config(self.config_data)

    # ======== 预设切换 ========
    def _on_provider_changed(self, choice: str) -> None:
        if not self._auto_save_enabled:
            self._update_delete_btn_visibility()
            return
        if choice in ('───── 我的预设 ─────', ''):
            return

        # 用户预设
        profiles = load_profiles()
        if choice in profiles:
            self._apply_ui_to_config()
            self._auto_save_enabled = False

            p = profiles[choice]
            # 加载预设的全部字段
            self._provider_var.set(choice)
            self._api_url_var.set(p.get('api_url', ''))
            self._api_key_var.set(p.get('api_key', ''))
            self._model_name_var.set(p.get('model_name', ''))
            self._temp_var.set(p.get('temperature', 0.3))
            self._temp_value_label.configure(text=f"{p.get('temperature', 0.3):.1f}")
            self._max_tokens_var.set(str(p.get('max_tokens', 2000)))
            self._system_prompt_text.delete('1.0', 'end')
            self._system_prompt_text.insert('1.0', p.get('system_prompt', ''))
            self._custom_rules_text.delete('1.0', 'end')
            self._custom_rules_text.insert('1.0', p.get('custom_rules', ''))
            self._extra_params_text.delete('1.0', 'end')
            self._extra_params_text.insert('1.0', p.get('extra_params', ''))
            self._poll_interval_var.set(str(p.get('poll_interval', 0.8)))

            self._update_delete_btn_visibility()
            self._last_provider_name = choice
            self._auto_save_enabled = True
            self._auto_save()
            return

        # 内置预设：保存当前字段到旧服务商，再加载新服务商
        # 注意：_provider_var 已被 OptionMenu 更新为新值，需用 _last_provider_name
        old_provider = self._last_provider_name
        new_provider = choice

        # 1. 将当前 UI 字段保存到旧服务商的 provider_configs
        if 'provider_configs' not in self.config_data:
            self.config_data['provider_configs'] = {}
        self.config_data['provider_configs'][old_provider] = {
            'api_url': self._api_url_var.get(),
            'api_key': self._api_key_var.get(),
            'model_name': self._model_name_var.get(),
        }

        # 2. 切换到新服务商
        switch_provider(self.config_data, new_provider)
        self._last_provider_name = new_provider

        # 3. 更新 UI
        self._auto_save_enabled = False
        self._api_url_var.set(self.config_data['api_url'])
        self._api_key_var.set(self.config_data['api_key'])
        self._model_name_var.set(self.config_data['model_name'])
        self._update_delete_btn_visibility()
        self._auto_save_enabled = True
        self._auto_save()

    # ======== 保存为预设 ========
    def _save_as_profile(self) -> None:
        self._apply_ui_to_config()
        save_config(self.config_data)

        dlg = ProfileNameDialog(self)
        self.wait_window(dlg)
        name = dlg.result
        if not name:
            return

        save_profile(name, self.config_data)
        self._refresh_provider_menu()

        self._auto_save_enabled = False
        self._provider_var.set(name)
        self._update_delete_btn_visibility()
        self._auto_save_enabled = True

        self._save_btn.configure(text='✅ 已保存', text_color=COLORS['accent_green'])
        self.after(1800, lambda: self._save_btn.configure(
            text='💾 保存为预设', text_color=COLORS['accent_blue'],
        ))

    # ======== 删除预设 ========
    def _delete_profile(self) -> None:
        name = self._provider_var.get()
        profiles = load_profiles()
        if name not in profiles:
            return

        dlg = ConfirmDialog(
            self, '删除预设', f'确定要删除预设 "{name}" 吗？此操作不可撤销。',
        )
        self.wait_window(dlg)
        if not dlg.result:
            return

        delete_profile(name)
        self._refresh_provider_menu()

        # 切回第一个内置预设
        first_builtin = list(PRESET_PROVIDERS.keys())[0]
        self._auto_save_enabled = False
        self._provider_var.set(first_builtin)
        switch_provider(self.config_data, first_builtin)
        self._api_url_var.set(self.config_data['api_url'])
        self._api_key_var.set(self.config_data['api_key'])
        self._model_name_var.set(self.config_data['model_name'])
        self._update_delete_btn_visibility()
        self._auto_save_enabled = True
        self._auto_save()

    # ======== 启动/停止监听 ========
    def _toggle_monitoring(self) -> None:
        if self._monitor.is_alive():
            self._monitor.stop()
            self._toggle_btn.configure(
                text='▶  启动监听',
                fg_color=COLORS['accent_green_dim'],
                hover_color='#1a7a37',
                text_color='#bbf7d0',
            )
            self._status_dot.configure(text_color=COLORS['accent_red'])
            self._status_label.configure(text='已停止')
        else:
            self._apply_ui_to_config()
            save_config(self.config_data)
            self._toggle_btn.configure(text='⏳ 正在测试连接...', state='disabled')
            self._status_label.configure(text='测试连接中...')
            threading.Thread(target=self._test_and_start, daemon=True).start()

    def _test_and_start(self) -> None:
        ok, msg = test_connection(self.config_data)
        if ok:
            self.after(0, lambda: self._do_start_monitoring())
            self.after(0, lambda: self._toast.show('API 连接成功', success=True))
        else:
            self.after(0, lambda: self._toggle_btn.configure(
                text='▶  启动监听', state='normal',
            ))
            self.after(0, lambda: self._status_label.configure(text='已停止'))
            self.after(0, lambda: self._toast.show(msg, success=False))

    def _do_start_monitoring(self) -> None:
        self._monitor = ClipboardMonitor()
        self._monitor.set_config(self.config_data)
        self._monitor.set_on_translate(self._on_translate_done)
        self._monitor.set_on_status(self._on_status_change)
        self._monitor.start()
        self._toggle_btn.configure(
            text='⏹  停止监听', state='normal',
            fg_color=COLORS['accent_red_dim'],
            hover_color='#991b1b',
            text_color='#fecaca',
        )
        self._status_dot.configure(text_color=COLORS['accent_green'])
        self._status_label.configure(text='运行中')

    def _on_translate_done(self, original: str, translated: str) -> None:
        self.after(0, self._toast.show)

    def _on_status_change(self, status: str) -> None:
        self.after(0, lambda: self._status_label.configure(text=status))

    # ======== 其他事件 ========
    def _toggle_key_visibility(self) -> None:
        if self._api_key_entry.cget('show') == '•':
            self._api_key_entry.configure(show='')
            self._eye_btn.configure(text='🙈')
        else:
            self._api_key_entry.configure(show='•')
            self._eye_btn.configure(text='👁')

    def _on_temp_changed(self, val: float) -> None:
        self._temp_value_label.configure(text=f'{val:.1f}')

    def _toggle_advanced(self) -> None:
        self._advanced_open = not self._advanced_open
        if self._advanced_open:
            self._adv_panel.pack(
                fill='x', padx=18, pady=(10, 0),
                after=self._adv_btn.master,
            )
            self._adv_btn.configure(text='收起高级参数  ▾')
        else:
            self._adv_panel.pack_forget()
            self._adv_btn.configure(text='高级参数  ▸')

    def _apply_ui_to_config(self) -> None:
        c = self.config_data
        c['api_provider'] = self._provider_var.get()
        c['api_url'] = self._api_url_var.get()
        c['api_key'] = self._api_key_var.get()
        c['model_name'] = self._model_name_var.get()
        c['temperature'] = round(self._temp_var.get(), 1)
        c['max_tokens'] = int(self._max_tokens_var.get() or 2000)
        c['system_prompt'] = self._system_prompt_text.get('1.0', 'end-1c')
        c['custom_rules'] = self._custom_rules_text.get('1.0', 'end-1c')
        c['extra_params'] = self._extra_params_text.get('1.0', 'end-1c')
        try:
            c['poll_interval'] = float(self._poll_interval_var.get() or 0.8)
        except ValueError:
            c['poll_interval'] = 0.8

    def _load_config_to_ui(self) -> None:
        c = self.config_data
        self._provider_var.set(c.get('api_provider', 'DeepSeek'))
        self._api_url_var.set(c.get('api_url', ''))
        self._api_key_var.set(c.get('api_key', ''))
        self._model_name_var.set(c.get('model_name', ''))
        self._temp_var.set(c.get('temperature', 0.3))
        self._temp_value_label.configure(text=f"{c.get('temperature', 0.3):.1f}")
        self._max_tokens_var.set(str(c.get('max_tokens', 2000)))
        self._system_prompt_text.insert('1.0', c.get('system_prompt', ''))
        self._custom_rules_text.insert('1.0', c.get('custom_rules', ''))
        self._extra_params_text.insert('1.0', c.get('extra_params', ''))
        self._poll_interval_var.set(str(c.get('poll_interval', 0.8)))
        self._update_delete_btn_visibility()

    def _open_history(self) -> None:
        HistoryWindow(self)


# ======== 深色风格弹窗 ========

class _BaseDialog(ctk.CTkToplevel):
    """自定义弹窗基类，匹配主界面风格"""

    def __init__(self, master, title: str, width=380, height=180):
        super().__init__(master)
        self.result = None
        self.title('')
        self.geometry(f'{width}x{height}')
        self.resizable(False, False)
        self.configure(fg_color=COLORS['bg_surface'])
        self.after(10, self._center_on_parent)

        # 标题栏
        title_bar = ctk.CTkFrame(
            self, fg_color=COLORS['bg_card'], height=40, corner_radius=0,
        )
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)
        ctk.CTkLabel(
            title_bar, text=title,
            font=('Microsoft YaHei', 13, 'bold'),
            text_color=COLORS['text_primary'],
        ).pack(side='left', padx=16, pady=8)

        # 内容区
        self._body = ctk.CTkFrame(self, fg_color='transparent')
        self._body.pack(fill='both', expand=True, padx=20, pady=16)

        # 确保弹窗在最前
        self.attributes('-topmost', True)
        self.grab_set()

    def _center_on_parent(self) -> None:
        parent = self.master
        px = parent.winfo_rootx() + parent.winfo_width() // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        self.geometry(f'+{px - self.winfo_width() // 2}+{py - self.winfo_height() // 2}')


class ProfileNameDialog(_BaseDialog):
    """保存预设命名弹窗"""

    def __init__(self, master):
        super().__init__(master, '保存预设', 420, 230)

        ctk.CTkLabel(
            self._body, text='请输入预设名称：',
            font=('Microsoft YaHei', 12),
            text_color=COLORS['text_secondary'],
        ).pack(anchor='w', pady=(8, 12))

        self._entry = _make_entry(self._body, ctk.StringVar(), '例如：工作用 DeepSeek')
        self._entry.pack(fill='x', pady=(0, 18))

        btn_row = ctk.CTkFrame(self._body, fg_color='transparent')
        btn_row.pack(fill='x')

        ctk.CTkButton(
            btn_row, text='取消', command=self.destroy,
            fg_color=COLORS['bg_card'], hover_color='#252d38',
            text_color=COLORS['text_secondary'],
            border_color=COLORS['border'], border_width=1,
            font=('Microsoft YaHei', 12), height=38, corner_radius=8,
        ).pack(side='left', fill='x', expand=True, padx=(0, 8))

        ctk.CTkButton(
            btn_row, text='确认保存', command=self._confirm,
            fg_color=COLORS['accent_blue_dim'], hover_color='#2a4a7a',
            text_color=COLORS['accent_blue'],
            border_color='#3a6aaa', border_width=1,
            font=('Microsoft YaHei', 12), height=38, corner_radius=8,
        ).pack(side='right', fill='x', expand=True, padx=(8, 0))

        self._entry.focus_set()
        self.bind('<Return>', lambda e: self._confirm())
        self.bind('<Escape>', lambda e: self.destroy())

    def _confirm(self) -> None:
        self.result = self._entry.get().strip()
        self.destroy()


class ConfirmDialog(_BaseDialog):
    """确认弹窗"""

    def __init__(self, master, title: str, message: str):
        super().__init__(master, title, 420, 190)

        ctk.CTkLabel(
            self._body, text=message,
            font=('Microsoft YaHei', 12),
            text_color=COLORS['text_primary'],
            wraplength=370, justify='left',
        ).pack(anchor='w', pady=(8, 18))

        btn_row = ctk.CTkFrame(self._body, fg_color='transparent')
        btn_row.pack(fill='x')

        ctk.CTkButton(
            btn_row, text='取消', command=self.destroy,
            fg_color=COLORS['bg_card'], hover_color='#252d38',
            text_color=COLORS['text_secondary'],
            border_color=COLORS['border'], border_width=1,
            font=('Microsoft YaHei', 12), height=38, corner_radius=8,
        ).pack(side='left', fill='x', expand=True, padx=(0, 8))

        ctk.CTkButton(
            btn_row, text='确认删除', command=self._confirm,
            fg_color=COLORS['accent_red_dim'], hover_color='#991b1b',
            text_color='#fecaca',
            border_color='#7f1d1d', border_width=1,
            font=('Microsoft YaHei', 12), height=38, corner_radius=8,
        ).pack(side='right', fill='x', expand=True, padx=(8, 0))

        self.bind('<Return>', lambda e: self._confirm())
        self.bind('<Escape>', lambda e: self.destroy())

    def _confirm(self) -> None:
        self.result = True
        self.destroy()


# ======== 历史记录窗口 ========
class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title('翻译历史记录')
        self.geometry('560x460')
        self.resizable(True, True)
        self.configure(fg_color=COLORS['bg_surface'])

        search_frame = ctk.CTkFrame(self, fg_color='transparent')
        search_frame.pack(fill='x', padx=14, pady=(14, 6))
        self._search_var = ctk.StringVar()
        self._search_var.trace('w', lambda *a: self._refresh())
        _make_entry(search_frame, self._search_var, '搜索原文或译文...').pack(fill='x')

        self._count_label = ctk.CTkLabel(
            self, text='', font=('Microsoft YaHei', 10),
            text_color=COLORS['text_muted'],
        )
        self._count_label.pack(anchor='w', padx=16, pady=(0, 6))

        self._list_frame = ctk.CTkScrollableFrame(self, fg_color='transparent')
        self._list_frame.pack(fill='both', expand=True, padx=12, pady=(0, 12))
        self._refresh()

    def _refresh(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()

        keyword = self._search_var.get().strip()
        records = search_records(keyword) if keyword else get_all_records()
        total = get_record_count()
        self._count_label.configure(
            text=f'共 {total} 条记录，当前显示 {len(records)} 条',
        )

        for r in records:
            card = ctk.CTkFrame(
                self._list_frame, fg_color=COLORS['bg_card'],
                border_color=COLORS['border'], border_width=1,
                corner_radius=8,
            )
            card.pack(fill='x', pady=3)

            header = ctk.CTkFrame(card, fg_color='transparent')
            header.pack(fill='x', padx=10, pady=(8, 2))
            ctk.CTkLabel(
                header, text=r['timestamp'],
                font=('Consolas', 10), text_color=COLORS['text_muted'],
            ).pack(side='left')

            del_btn = ctk.CTkButton(
                header, text='✕', width=24, height=24,
                fg_color='transparent', hover_color='#4a1515',
                text_color=COLORS['text_muted'],
                font=('Microsoft YaHei', 12),
                command=lambda rid=r['id']: self._delete_record(rid),
            )
            del_btn.pack(side='right')

            ctk.CTkLabel(
                card, text=f"原文: {r['original_text']}",
                font=('Microsoft YaHei', 11),
                text_color=COLORS['text_primary'],
                anchor='w', justify='left', wraplength=500,
            ).pack(fill='x', padx=10, pady=(0, 2))

            ctk.CTkLabel(
                card, text=f"译文: {r['translated_text']}",
                font=('Microsoft YaHei', 11),
                text_color=COLORS['accent_blue'],
                anchor='w', justify='left', wraplength=500,
            ).pack(fill='x', padx=10, pady=(0, 8))

    def _delete_record(self, record_id: int) -> None:
        delete_record(record_id)
        self._refresh()
