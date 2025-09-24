import httpx, re
import astrbot.api.message_components as Comp

async def get_public_recruitment_data():
    """异步获取所有可公开招募的干员数据。"""
    url = "https://prts.wiki/api.php"
    params = {
        "action": "cargoquery",
        "format": "json",
        "tables": "chara,char_obtain",
        "limit": "5000",
        "fields": "chara.profession,chara.position,chara.rarity,chara.tag,chara.cn",
        "where": "char_obtain.obtainMethod LIKE '%公开招募%'",
        "join_on": "chara._pageName=char_obtain._pageName"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            recruitment_data_cache = [item["title"] for item in data.get("cargoquery", [])]
            return recruitment_data_cache
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        print(f"数据获取失败，请检查网络连接或API状态。错误: {e}")
        return None


async def format_operator(op):
    """格式化单个干员信息"""
    name = op.get("cn", "未知干员")
    rarity = "★" * (int(op.get("rarity", 0)) + 1)
    profession = op.get("profession", "未知职业")
    position = op.get("position", "未知位置")
    tags = op.get("tag", "无标签")
    
    return {
        "name": name,
        "rarity": rarity,
        "profession": profession,
        "position": position,
        "tags": tags
    }


async def main(tags: str):
    """主函数，负责用户交互和数据处理。"""
    user_input = tags
    tags = re.split(r'[\s,，]+', user_input)
    input_tags = [tag.strip() for tag in tags if tag.strip()]
    if not input_tags:
        e = "您没有输入任何标签。"
        raise e

    operators_data = await get_public_recruitment_data()
    if not operators_data:
        e = "无法获取公开招募干员数据。"
        raise e
    matched_operators_all = []
    matched_operators_single = {tag: [] for tag in input_tags}  # 每个标签下单独匹配的干员
    # 遍历所有干员数据，进行匹配
    for operator in operators_data:
        # 获取干员的标签字符串
        operator_tags_str = operator.get("tag", "")
        # 统计该干员匹配了多少个输入标签
        matched_tag_count = 0
        for tag in input_tags:
            if tag in operator_tags_str:
                matched_tag_count += 1
        # 完全匹配：干员同时具有所有输入标签
        if matched_tag_count == len(input_tags):
            matched_operators_all.append(operator)
        # 部分匹配：只匹配部分标签
        elif matched_tag_count > 0:
            # 对于每个匹配的标签，将该干员添加到对应的列表中
            for tag in input_tags:
                if tag in operator_tags_str:
                    matched_operators_single[tag].append(operator)

    # 构建返回结果
    result = {
        "full_match": [await format_operator(op) for op in matched_operators_all],
        "single_tag_match": {}
    }
    
    # 按照输入标签的顺序处理单个标签匹配的干员
    for tag in input_tags:
        operators = matched_operators_single[tag]
        # 从单标签匹配列表中排除那些也出现在完全匹配列表中的干员
        unique_operators = [op for op in operators if op not in matched_operators_all]
        result["single_tag_match"][tag] = [await format_operator(op) for op in unique_operators]
    # 构建消息内容列表，每个tag一个Plain组件
    content_list = []
    # 添加完全匹配部分的消息
    full_match_msg = "找到以下完全匹配的干员：\n"
    if result["full_match"]:
        for op in result["full_match"]:
            full_match_msg += "-" * 10 + "\n"
            full_match_msg += f"干员: {op['name']}\n"
            full_match_msg += f"星级: {op['rarity']}\n"
            full_match_msg += f"职业: {op['profession']}\n"
            full_match_msg += f"位置: {op['position']}\n"
            full_match_msg += f"标签: {op['tags']}\n"
    else:
        full_match_msg += "暂无完全匹配的干员。\n"
    # 为完全匹配部分创建Plain组件
    content_list.append(Comp.Plain(full_match_msg))

    # 为每个标签创建独立的Plain组件
    for tag, operators in result["single_tag_match"].items():
        single_match_msg = f"\n标签 '{tag}' 匹配的干员：\n"
        if operators:
            for op in operators:
                single_match_msg += "-" * 10 + "\n"
                single_match_msg += f"干员: {op['name']}\n"
                single_match_msg += f"星级: {op['rarity']}\n"
                single_match_msg += f"职业: {op['profession']}\n"
                single_match_msg += f"位置: {op['position']}\n"
                single_match_msg += f"标签: {op['tags']}\n"
        else:
            single_match_msg += "无匹配干员\n"
        # 为每个标签创建独立的Plain组件
        content_list.append(Comp.Plain(single_match_msg))
    return content_list
