from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import sys
import os

# 添加当前插件目录到sys.path，确保可以导入同目录下的模块
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

# 引用你原来的模块（请确保这些模块位于插件目录，或在 sys.path 中可导入）
import ganyuan_info
import qita_info


@register("ark_info_search", "wxgl", "干员信息/道具查询插件", "0.1.0", "https://github.com/wxgl/ark_info_search")
class ArkInfoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.ctx = context
        logger.info("ArkInfoPlugin 已初始化")

    @filter.command("arkhelp")
    async def arkhelp(self, event: AstrMessageEvent):
        """帮助指令：/arkhelp 显示可用命令"""
        help_text = (
            "可用指令：\n"
            "/arkgy <干员名> - 查询干员信息（例如：/arkgy 娜仁图亚）\n"
            "/arkqt <物品名> - 查询信物/道具信息（例如：/arkqt 娜仁图亚的信物）\n"
            "/arkhelp - 显示此帮助"
        )
        yield event.plain_result(help_text)

    @filter.command("arkgy")
    async def ganyuan(self, event: AstrMessageEvent, name: str):
        """查询干员信息：/arkgy 娜仁图亚"""
        try:
            # 直接异步调用，不再需要线程池
            result = await ganyuan_info.main(name)
            if not result:
                yield event.plain_result(f"未找到干员：{name}")
                return
            name_out, zhi_ye, fen_zhi, xing_ji, te_xing, te_xing_b = result
            text = (
                f"干员：{name_out}\n"
                f"职业：{zhi_ye}\n"
                f"分支：{fen_zhi}\n"
                f"星级：{xing_ji}\n"
                f"特性：{te_xing}\n"
                f"特性备注：{te_xing_b}"
            )
            yield event.plain_result(text)
        except Exception as e:
            logger.exception("查询干员信息出错")
            yield event.plain_result(f"查询干员信息时发生错误：{e}")

    @filter.command("arkqt")
    async def qita(self, event: AstrMessageEvent, name: str):
        """查询其他信息（信物等）：/arkqt 娜仁图亚的信物"""
        try:
            # 直接异步调用
            result = await qita_info.main(name)
            if not result:
                yield event.plain_result(f"未找到条目：{name}")
                return
            qita_name, miao_shu, yong_tu, huode_fangshi, fen_lei = result
            text = (
                f"名称：{qita_name}\n"
                f"介绍：{miao_shu}\n"
                f"用途：{yong_tu}\n"
                f"获得方式：{huode_fangshi}\n"
                f"分类：{fen_lei}"
            )
            yield event.plain_result(text)
        except Exception as e:
            logger.exception("查询其他信息出错")
            yield event.plain_result(f"查询条目信息时发生错误：{e}")

    async def terminate(self):
        """插件被卸载/停用时会调用"""
        logger.info("ArkInfoPlugin 被终止")