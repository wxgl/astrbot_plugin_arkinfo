import re
from astrbot.api import logger
import astrbot.api.message_components as Comp
from . import search_model
from collections import namedtuple

OtherthingInfo = namedtuple('OtherthingInfo',
                            ['image_url', 'other_thing_name', 'description', 'yong_tu', 'get_manner',
                             'fen_lei'])

# 预编译字段正则表达式
FIELD_PATTERNS_OTHER = [
    ('description', re.compile(r"\|描述\s*=\s*(.+)"), lambda x: x.strip()),
    ('yong_tu', re.compile(r"\|用途\s*=\s*(.+)"), lambda x: x.strip()),
    ('get_manner', re.compile(r"\|获得方式\s*=\s*(.+)"), lambda x: x.strip()),
    ('fen_lei', re.compile(r"\|分类\s*=\s*(.+)"), lambda x: x.strip())
]


async def get_other_image(name: str):
    """异步获取道具的image"""
    if not name:
        return []
    name = f"文件:道具 带框 {name}.png"
    return await search_model.get_images_url([name])


async def clean_over_wiki(other_thing_name):
    try:
        other_thing_name = await search_model.search_wikitext(other_thing_name)
        other_thing_name, wikitext = await search_model.get_wikitext(other_thing_name)
        image_url = await get_other_image(other_thing_name)
        if not wikitext:
            return None
        # 批量处理正则表达式查找和结果处理
        results = {}
        for field_name, pattern, process_func in FIELD_PATTERNS_OTHER:
            match = pattern.search(wikitext)
            if match:
                results[field_name] = process_func(match.group(1))
            else:
                results[field_name] = None
        return OtherthingInfo(image_url, other_thing_name, results['description'], results['yong_tu'],
                              results['get_manner'], results['fen_lei'])
    except (search_model.httpx.HTTPStatusError, search_model.httpx.RequestError) as e:
        logger.error(f"获取信息失败: {e}")
        return None
    except Exception as e:
        logger.error(f"获取信息时发生未知错误: {e}")
        raise e


async def main(other_thing_name: str):
    # other_thing_name = "娜仁图亚的信物"
    """
    result含有的参数（按顺序）：
    other_thing_name, description, yong_tu, get_manner, fen_lei
    """
    result = await clean_over_wiki(other_thing_name)
    chain = None
    plain = None
    if not result:
        plain = f"未找到条目：{other_thing_name}"
    else:
        # 检查是否有图片URL并确保它是有效的
        image_url = ""
        if (result.image_url and isinstance(result.image_url, list) 
            and len(result.image_url) > 0 and result.image_url[0]):
            image_url = result.image_url[0]  # 取第一张图片
            
        components = []
        # 只有当图片URL有效时才添加图片组件
        if image_url:
            components.append(Comp.Image.fromURL(image_url))
        components.append(Comp.Plain(f"名称：{result.other_thing_name or '未知'}\n"
                   f"介绍：{result.description or '无'}\n"
                   f"用途：{result.yong_tu or '无'}\n"
                   f"获得方式：{result.get_manner or '未知'}\n"
                   f"分类：{result.fen_lei or '未知'}"
                   ))
        chain = components
    return chain, plain
