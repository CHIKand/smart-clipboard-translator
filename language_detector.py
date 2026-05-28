"""中文文本检测工具"""

import re

# 中文字符 Unicode 范围：基本汉字 + 扩展区
_CJK_PATTERN = re.compile(r'[一-鿿㐀-䶿豈-﫿]')


def contains_chinese(text: str) -> bool:
    """检查文本是否包含中文字符"""
    if not text:
        return False
    return bool(_CJK_PATTERN.search(text))


def is_mainly_chinese(text: str) -> bool:
    """检查文本主体是否为中文（中文字符占比 > 30%）"""
    if not text:
        return False
    chinese_chars = len(_CJK_PATTERN.findall(text))
    total_chars = len(re.sub(r'\s', '', text))
    if total_chars == 0:
        return False
    return (chinese_chars / total_chars) > 0.3
