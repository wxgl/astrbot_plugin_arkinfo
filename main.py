from . import ganyuan, other_thing, gongzhao_model, stage_enemy, search_model
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp


@register("akn_info_search", "wxgl", "干员信息/道具查询插件", "0.1.0", "https://github.com/wxgl/akn_info_search")
class AknInfoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.ctx = context
        logger.info("AknInfoPlugin 已初始化")

    @filter.command("aknhelp")
    async def aknhelp(self, event: AstrMessageEvent):
        """帮助指令：/aknhelp 显示可用命令"""
        help_text = (
            "可用指令：\n"
            "获取干员信息（支持时装立绘，默认精二图）:\n"
            "   /akngy, /aknop <干员名，（时装/皮肤）1>\n "
            "       如：（玛恩纳，时装1）,（玛恩纳 皮肤1）等\n"
            "   精确：娜仁图亚，低级模糊：娜仁（需从开头连贯）\n"
            "\n公招（gz）查询(仅aiocqhttp)，tag如：治疗，防护\n"
            "   /akngz\n"
            "\n获取其他（qt）信息（如：娜仁图亚的信物）:\n"
            "   /aknqt, /aknoth\n"
            "\n关卡（st）及敌人（dr）查询:\n"
            "   /akndr, /akngq, /aknen, /aknst"
        )
        yield event.plain_result(help_text)
        return

    @filter.command("akngy", alias={'aknop'})
    async def ganyuan(self, event: AstrMessageEvent, name: str):
        """查询干员信息：/akngy 娜仁图亚"""
        try:
            chain, plain = await ganyuan.main(name)
            if chain is not None:
                yield event.chain_result(chain)
            elif plain is not None:
                yield event.plain_result(plain)
            else:
                plain = "未知错误"
                yield event.plain_result(plain)
            return
        except (search_model.httpx.HTTPStatusError, search_model.httpx.RequestError) as e:
            logger.error(f"获取信息失败: {e}")
            yield event.plain_result(f"获取信息失败: {e}")
            return
        except Exception as e:
            logger.error(f"获取信息时发生未知错误: {e}")
            yield event.plain_result(f"获取信息时发生未知错误: {e}")
            return

    @filter.command("akngz")  # 待完善
    async def gongzhao(self, event: AstrMessageEvent, tags: str):
        """查询公招信息：/akngz"""
        try:
            content_list = await gongzhao_model.main(tags)
            node = Comp.Node(uin=375263390,
                             name="我习惯了",
                             content=content_list)
            yield event.chain_result([node])
        except (search_model.httpx.HTTPStatusError, search_model.httpx.RequestError) as e:
            logger.error(f"获取信息失败: {e}")
            yield event.plain_result(f"获取信息失败: {e}")
            return
        except Exception as e:
            yield event.plain_result(f"{e}")
            return

    @filter.command("aknqt", alias={'aknoth'})
    async def qita(self, event: AstrMessageEvent, name: str):
        """查询其他信息（信物等）：/aknqt 娜仁图亚的信物"""
        try:
            chain, plain = await other_thing.main(name)
            if chain is not None:
                yield event.chain_result(chain)
            elif plain is not None:
                yield event.plain_result(plain)
            else:
                plain = "未知错误"
                yield event.plain_result(plain)
            return
        except (search_model.httpx.HTTPStatusError, search_model.httpx.RequestError) as e:
            logger.error(f"获取信息失败: {e}")
            yield event.plain_result(f"获取信息失败: {e}")
            return
        except Exception as e:
            logger.error(f"获取信息时发生未知错误: {e}")
            yield event.plain_result(f"获取信息时发生未知错误: {e}")
            return


    @filter.command("akndr", alias={'akndr', 'akngq', 'aknen', 'aknst'})
    async def dr(self, event: AstrMessageEvent, name: str):
        """查询关卡，敌人信息"""
        try:
            enemy_msg, all_enemy_msg, once_enemy_in_stage_msg = await stage_enemy.main(name)
            if enemy_msg:
                yield event.chain_result(enemy_msg)
            elif all_enemy_msg:
                node = Comp.Node(uin=375263390,
                                 name="我习惯了",
                                 content=all_enemy_msg)
                yield event.chain_result([node])
            elif once_enemy_in_stage_msg:
                node = Comp.Node(uin=375263390,
                                 name="我习惯了",
                                 content=once_enemy_in_stage_msg)
                yield event.chain_result([node])
            else:
                plain = "未知错误"
                yield event.plain_result(plain)
            return

        except (search_model.httpx.HTTPStatusError, search_model.httpx.RequestError) as e:
            logger.error(f"获取信息失败: {e}")
            yield event.plain_result(f"获取信息失败: {e}")
            return
        except Exception as e:
            logger.error(f"获取信息时发生未知错误: {e}")
            yield event.plain_result(f"获取信息时发生未知错误: {e}")
            return

    async def terminate(self):
        """插件被卸载/停用时会调用"""
        await search_model.close_http_client()
        logger.info("AknInfoPlugin 被终止")
