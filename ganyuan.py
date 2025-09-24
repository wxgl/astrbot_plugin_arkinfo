import re
from astrbot.api import logger
import astrbot.api.message_components as Comp
from . import search_model
from collections import namedtuple

OperatorInfo = namedtuple('OperatorInfo',
                          ['name', 'zhi_ye', 'fen_zhi', 'xing_ji', 'te_xing', 'te_xing_b',
                           'wikitext'])
""" 待完善
"name": "干员名称",
"zhi_ye": "职业",
"fen_zhi": "分支",
"xing_ji": "稀有度",
"te_xing": "特性",
"te_xing_b": "特性备注",
"wikitext": "wikitext"
"""

# 预编译正则表达式以提高性能
COLOR_PATTERN = re.compile(r'\{\{color\|#[0-9A-F]{6}\|(.*?)}}')
LINK_PATTERN_1 = re.compile(r'\[\[([^]|]+)\|([^]]+)]]')
LINK_PATTERN_2 = re.compile(r'\[\[([^]]+)]]')
BOLD_ITALIC_PATTERN = re.compile(r"''+(.*?)''+")


def clean_wikitext(text):
    """清理wikitext中的标记，提取纯文本内容（同步版本）"""
    if not text:
        return ""  # 返回空字符串而不是None

    # 移除颜色标记 {{color|#00B0FF|回旋投射物}}
    text = COLOR_PATTERN.sub(r'\1', text)

    # 移除其他常见的wikitext标记
    text = LINK_PATTERN_1.sub(r'\2', text)  # [[链接|显示文字]] -> 显示文字
    text = LINK_PATTERN_2.sub(r'\1', text)  # [[链接]] -> 链接
    text = BOLD_ITALIC_PATTERN.sub(r'\1', text)  # 移除粗体和斜体标记
    text = text.replace('*', '')
    return text.strip()


# 预编译字段正则表达式
FIELD_PATTERNS = {
    'zhi_ye': re.compile(r"\|职业\s*=\s*(.+)"),
    'fen_zhi': re.compile(r"\|分支\s*=\s*(.+)"),
    'xing_ji': re.compile(r"\|稀有度\s*=\s*(.+)"),
    'te_xing': re.compile(r"\|特性\s*=\s*(.+)"),
    'te_xing_b': re.compile(r"\|特性备注\s*=\s*\s*(.+)"),
}


async def get_operator_image(name: str, skin):
    """异步获取干员的image，默认为精二皮"""
    if not name:
        return []
    if "时装" or "皮肤" in skin:
        skin = re.sub("时装|皮肤", "skin", skin)
    name = f"文件:立绘 {name} {skin}.png"
    return await search_model.get_images_url([name])


async def get_operator_info_concurrently(name: str, skin="2"):
    """并发获取干员信息和图片，提高处理速度"""
    try:
        name = await search_model.search_wikitext(name)
        name_out, wikitext = await search_model.get_wikitext(name)
        image_url = await get_operator_image(name, skin)
        return name_out, wikitext, image_url
    except Exception as e:
        logger.error(f"获取信息时出错: {e}")
        raise e


async def clean_over_wiki(ganyuan, skin):
    try:
        # 并发获取干员信息和图片，提高处理速度
        name, wikitext, image= await get_operator_info_concurrently(ganyuan, skin)
        if not wikitext:
            return image
        # 批量处理正则表达式查找和结果处理
        results = {}
        for field_name, pattern in FIELD_PATTERNS.items():
            match = pattern.search(wikitext)
            if match:
                raw_value = match.group(1)
                if field_name in ['zhi_ye', 'fen_zhi', 'te_xing', 'te_xing_b']:
                    # 直接同步处理wikitext清理，避免异步开销
                    results[field_name] = clean_wikitext(raw_value)
                elif field_name == 'xing_ji':
                    # 处理稀有度
                    results[field_name] = "★" * (int(raw_value.strip()) + 1)
                else:
                    results[field_name] = raw_value
            else:
                results[field_name] = None
        # 返回图片和操作员信息
        return image, OperatorInfo(name, results['zhi_ye'], results['fen_zhi'],
                                   results['xing_ji'], results['te_xing'], results['te_xing_b'], wikitext)
    except Exception as e:
        logger.error(f"处理信息时出错: {e}")
        raise e

async def main(ganyuan=None):
    try:
        if ganyuan is None:
            plain = "请输入内容"
            return  plain
        # ganyuan = "娜仁图亚"
        """
        result含有的参数（按顺序）：
        name, zhi_ye, fen_zhi, xing_ji, te_xing, te_xing_b, wikitext
        """
        parts = re.split(r'[\s,，]+', ganyuan)
        parts = [part.strip() for part in parts if part.strip()]
        # 确保即使只有一个参数也能正常工作
        name_part = parts[0] if parts else ""
        skin_part = parts[1] if len(parts) > 1 else "2"  # 默认皮肤为"2"
        image, result = await clean_over_wiki(name_part, skin_part)
        chain = None
        plain = None
        # 检查是否有图片URL并确保它是有效的
        image_url = ""
        if image and isinstance(image, list) and len(image) > 0 and image[0]:
            image_url = image[0]  # 取第一张图片
        
        if result is None:
            plain = Comp.Plain("未找到该干员信息")
        elif result.te_xing_b is None:
            components = []
            # 只有当图片URL有效时才添加图片组件
            if image_url:
                components.append(Comp.Image.fromURL(image_url))
            components.append(Comp.Plain(f"干员：{result.name or '未知'}\n"
                       f"职业：{result.zhi_ye or '未知'}\n"
                       f"分支：{result.fen_zhi or '未知'}\n"
                       f"稀有度：{result.xing_ji or '未知'}\n"
                       f"特性：{result.te_xing or '未知'}\n"
                       ))
            chain = components
        elif result.te_xing_b is not None:
            components = []
            # 只有当图片URL有效时才添加图片组件
            if image_url:
                components.append(Comp.Image.fromURL(image_url))
            components.append(Comp.Plain(f"干员：{result.name or '未知'}\n"
                       f"职业：{result.zhi_ye or '未知'}\n"
                       f"分支：{result.fen_zhi or '未知'}\n"
                       f"稀有度：{result.xing_ji or '未知'}\n"
                       f"特性：{result.te_xing or '未知'}\n"
                       f"特性备注：{result.te_xing_b or '无'}"
                       ))
            chain = components
        else:
            plain = Comp.Plain("没有找到该干员")
        return chain, plain
    except Exception as e:
        logger.error(f"处理信息时出错: {e}")
        raise e