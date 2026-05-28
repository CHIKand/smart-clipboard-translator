"""配置文件管理"""

import os
import json

CONFIG_DIR = os.path.join(os.getenv('APPDATA', ''), 'SmartClipboardTranslator')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.json')
PROFILES_PATH = os.path.join(CONFIG_DIR, 'profiles.json')

# 国内 AI 厂商 API 预设
PRESET_PROVIDERS = {
    'DeepSeek': {
        'api_url': 'https://api.deepseek.com',
        'model_name': 'deepseek-v4-flash',
    },
    '通义千问 (阿里)': {
        'api_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'model_name': 'qwen3-plus',
    },
    '智谱 GLM': {
        'api_url': 'https://open.bigmodel.cn/api/paas/v4/',
        'model_name': 'glm-4.7',
    },
    '月之暗面 Kimi': {
        'api_url': 'https://api.moonshot.ai/v1',
        'model_name': 'moonshot-v1-8k',
    },
    '豆包 (字节)': {
        'api_url': 'https://ark.cn-beijing.volces.com/api/v3',
        'model_name': 'doubao-seed-2.0-lite',
    },
    '零一万物': {
        'api_url': 'https://api.lingyiwanwu.com/v1',
        'model_name': 'yi-medium',
    },
}

DEFAULT_SYSTEM_PROMPT = (
    '你是一个专业的中译英翻译助手。'
    '请将用户输入的中文准确、流畅地翻译成英文。'
    '只输出译文，不要添加任何解释或额外内容。'
)

DEFAULT_CONFIG = {
    'api_provider': 'DeepSeek',
    'api_url': 'https://api.deepseek.com',
    'api_key': '',
    'model_name': 'deepseek-v4-flash',
    'provider_configs': {},
    'temperature': 0.3,
    'max_tokens': 2000,
    'system_prompt': DEFAULT_SYSTEM_PROMPT,
    'custom_rules': '',
    'extra_params': '',
    'poll_interval': 0.8,
}


def _get_provider_default(provider: str) -> dict:
    """获取服务商的默认 URL 和模型名"""
    if provider in PRESET_PROVIDERS:
        return {
            'api_url': PRESET_PROVIDERS[provider]['api_url'],
            'api_key': '',
            'model_name': PRESET_PROVIDERS[provider]['model_name'],
        }
    return {'api_url': '', 'api_key': '', 'model_name': ''}


def load_config() -> dict:
    """加载配置，自动迁移旧格式"""
    if not os.path.exists(CONFIG_PATH):
        return dict(DEFAULT_CONFIG)

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            saved = json.load(f)
    except (json.JSONDecodeError, IOError):
        return dict(DEFAULT_CONFIG)

    config = dict(DEFAULT_CONFIG)
    config.update(saved)

    # 兼容旧格式：没有 provider_configs 时，从顶层字段迁移
    if 'provider_configs' not in saved:
        provider = config.get('api_provider', 'DeepSeek')
        config['provider_configs'] = {}
        # 只在非默认值时迁移
        if config.get('api_url') or config.get('api_key'):
            config['provider_configs'][provider] = {
                'api_url': config.get('api_url', ''),
                'api_key': config.get('api_key', ''),
                'model_name': config.get('model_name', ''),
            }

    # 确保当前服务商的顶层字段正确（从 provider_configs 恢复）
    _resolve_provider_to_top(config)

    # 清理之前 bug 版本的脏数据（只保留 DeepSeek）
    _clean_provider_configs(config)

    return config


def _clean_provider_configs(config: dict) -> None:
    """清理脏数据：只保留 DeepSeek 的配置，删除其余（一次性修复旧版本 bug）"""
    pcs = config.get('provider_configs', {})
    if 'DeepSeek' in pcs:
        config['provider_configs'] = {'DeepSeek': pcs['DeepSeek']}
    else:
        config['provider_configs'] = {}


def _resolve_provider_to_top(config: dict) -> None:
    """将当前服务商配置写入顶层字段"""
    provider = config.get('api_provider', 'DeepSeek')
    pconfigs = config.get('provider_configs', {})
    if provider in pconfigs:
        pc = pconfigs[provider]
        config['api_url'] = pc.get('api_url', '')
        config['api_key'] = pc.get('api_key', '')
        config['model_name'] = pc.get('model_name', '')
    else:
        default = _get_provider_default(provider)
        config['api_url'] = default['api_url']
        config['api_key'] = default['api_key']
        config['model_name'] = default['model_name']


def save_provider_to_config(config: dict) -> None:
    """将当前顶层字段存入 provider_configs"""
    provider = config.get('api_provider', 'DeepSeek')
    if 'provider_configs' not in config:
        config['provider_configs'] = {}
    config['provider_configs'][provider] = {
        'api_url': config.get('api_url', ''),
        'api_key': config.get('api_key', ''),
        'model_name': config.get('model_name', ''),
    }


def switch_provider(config: dict, new_provider: str) -> dict:
    """切换服务商：先保存当前，再加载新的"""
    save_provider_to_config(config)
    config['api_provider'] = new_provider
    _resolve_provider_to_top(config)
    return config


def save_config(config: dict) -> None:
    """保存配置到文件"""
    save_provider_to_config(config)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ======== 用户预设管理 ========

def load_profiles() -> dict[str, dict]:
    """加载所有用户保存的配置预设"""
    if not os.path.exists(PROFILES_PATH):
        return {}
    try:
        with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_profile(name: str, config: dict) -> None:
    """保存一个命名配置预设"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    profiles = load_profiles()
    profiles[name] = {
        'api_provider': config.get('api_provider', ''),
        'api_url': config.get('api_url', ''),
        'api_key': config.get('api_key', ''),
        'model_name': config.get('model_name', ''),
        'temperature': config.get('temperature', 0.3),
        'max_tokens': config.get('max_tokens', 2000),
        'system_prompt': config.get('system_prompt', ''),
        'custom_rules': config.get('custom_rules', ''),
        'extra_params': config.get('extra_params', ''),
        'poll_interval': config.get('poll_interval', 0.8),
    }
    with open(PROFILES_PATH, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)


def delete_profile(name: str) -> None:
    """删除一个命名配置预设"""
    profiles = load_profiles()
    if name in profiles:
        del profiles[name]
        with open(PROFILES_PATH, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
