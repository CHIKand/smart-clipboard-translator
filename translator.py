"""翻译 API 调用模块"""

import json
import requests


def _build_payload(text: str, config: dict) -> dict:
    """构建 API 请求体"""
    system_content = config.get('system_prompt', '')
    custom_rules = config.get('custom_rules', '').strip()
    if custom_rules:
        system_content += f'\n\n用户翻译偏好：\n{custom_rules}'

    payload = {
        'model': config['model_name'],
        'messages': [
            {'role': 'system', 'content': system_content},
            {'role': 'user', 'content': text},
        ],
        'temperature': config.get('temperature', 0.3),
        'max_tokens': config.get('max_tokens', 2000),
    }

    extra_params = config.get('extra_params', '').strip()
    if extra_params:
        try:
            payload.update(json.loads(extra_params))
        except json.JSONDecodeError:
            pass
    return payload


def test_connection(config: dict) -> tuple[bool, str]:
    """测试 API 连接是否正常，返回 (成功, 消息)"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config["api_key"]}',
    }
    payload = _build_payload('Hello', config)
    # 测试连接时限制 token 消耗
    payload['max_tokens'] = 5
    try:
        response = requests.post(
            config['api_url'],
            headers=headers,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return True, 'API 连接成功'
    except requests.exceptions.Timeout:
        return False, 'API 连接超时'
    except requests.exceptions.HTTPError as e:
        return False, f'API 返回错误: {e.response.status_code}'
    except requests.exceptions.ConnectionError:
        return False, '无法连接到 API 服务器'
    except Exception as e:
        return False, f'连接失败: {e}'


def translate(text: str, config: dict) -> str:
    """调用大模型 API 翻译中文到英文"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config["api_key"]}',
    }
    payload = _build_payload(text, config)

    response = requests.post(
        config['api_url'],
        headers=headers,
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    return data['choices'][0]['message']['content'].strip()
