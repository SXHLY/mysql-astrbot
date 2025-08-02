import asyncio
import os
import sys
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 添加当前目录到系统路径
sys.path.insert(0, current_dir)

# 从同目录导入自定义模块
from mydb_connector import MySQLConnector


class MySQLCommandsPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.db = None
        asyncio.create_task(self.initialize_db())

    async def initialize_db(self):
        try:
            # 使用插件目录下的配置文件
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mysqlconfig.ini")
            self.db = MySQLConnector(config_path)
            logger.info("✅ MySQL数据库连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {str(e)}")

    @filter.command("addcmd", permission_type=filter.PermissionType.ADMIN)
    async def add_command(self, event: AstrMessageEvent, name: str, *, content: str):
        """添加新指令到数据库
        用法: /addcmd <指令名称> <指令内容>
        """
        if not self.db:
            yield event.plain_result("❌ 数据库未连接")
            return

        try:
            query = "INSERT INTO commands (name, command_content) VALUES (%s, %s)"
            self.db.execute_update(query, (name, content))
            yield event.plain_result(f"✅ 指令 '{name}' 已添加")
        except Exception as e:
            yield event.plain_result(f"❌ 添加失败: {str(e)}")

    @filter.command("runcmd")
    async def run_command(self, event: AstrMessageEvent, name: str):
        """执行数据库中的指令
        用法: /runcmd <指令名称>
        """
        if not self.db:
            yield event.plain_result("❌ 数据库未连接")
            return

        try:
            query = "SELECT command_content FROM commands WHERE name = %s"
            result = self.db.execute_query(query, (name,))

            if result:
                command_content = result[0][0]
                # 实际执行指令的逻辑
                yield event.plain_result(f"🔧 执行指令: {command_content}")

                # 示例：根据不同指令执行不同操作
                if "reboot" in command_content.lower():
                    yield event.plain_result("🔄 正在执行重启操作...")
                    # 这里添加实际的重启逻辑
                elif "status" in command_content.lower():
                    yield event.plain_result("📊 正在获取系统状态...")
                    # 这里添加获取状态的逻辑
            else:
                yield event.plain_result(f"⚠️ 未找到指令: {name}")
        except Exception as e:
            yield event.plain_result(f"❌ 执行失败: {str(e)}")

    @filter.command("listcmds")
    async def list_commands(self, event: AstrMessageEvent):
        """列出所有可用指令
        用法: /listcmds
        """
        if not self.db:
            yield event.plain_result("❌ 数据库未连接")
            return

        try:
            result = self.db.execute_query("SELECT name, command_content FROM commands")
            if not result:
                yield event.plain_result("📭 数据库中没有存储的指令")
                return

            commands_list = "\n".join([f"- {cmd[0]}: {cmd[1][:30]}..." for cmd in result])
            yield event.plain_result(f"📋 可用指令:\n{commands_list}")
        except Exception as e:
            yield event.plain_result(f"❌ 查询失败: {str(e)}")

    @filter.command("delcmd", permission_type=filter.PermissionType.ADMIN)
    async def delete_command(self, event: AstrMessageEvent, name: str):
        """删除数据库中的指令
        用法: /delcmd <指令名称>
        """
        if not self.db:
            yield event.plain_result("❌ 数据库未连接")
            return

        try:
            query = "DELETE FROM commands WHERE name = %s"
            count = self.db.execute_update(query, (name,))

            if count > 0:
                yield event.plain_result(f"🗑️ 指令 '{name}' 已删除")
            else:
                yield event.plain_result(f"⚠️ 未找到指令: {name}")
        except Exception as e:
            yield event.plain_result(f"❌ 删除失败: {str(e)}")

    async def terminate(self):
        if self.db:
            self.db.close()
            logger.info("🔌 数据库连接已关闭")


# 新的插件注册方式
def setup(plugin_manager):
    plugin_manager.register_star(
        "astrbot_plugin_mysql_commands",
        MySQLCommandsPlugin,
        author="是小火龙压",
        description="MySQL指令管理插件",
        version="Alpha-v0.1",
        repo_url="https://github.com/SXHLY/mysql-astrbot"
    )