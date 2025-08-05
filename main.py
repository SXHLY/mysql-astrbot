from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("mysql-interaction", "是小火龙压", "与mysql交互", "1.0.0", "https://github.com/SXHLY/mysql-astrbot")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        '''这是一个 hello world 指令''' # 这是 handler 的描述，将会被解析方便用户了解插件内容。非常建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 获取消息的纯文本内容
        logger.info("触发hello world指令!")
        yield event.plain_result(f"Hello, {user_name}!") # 发送一条纯文本消息