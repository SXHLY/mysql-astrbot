import configparser
import pymysql

class MySQLConnector:
    def __init__(self,config_file='mysql.ini'):
        """
        初始化MySQL连接器

        参数:
            config_file: MySQL配置文件路径，默认为'mysql.ini'
        """
        # 创建配置解析器并读取配置文件
        config = configparser.ConfigParser()
        config.read(config_file)
        # 使用配置信息建立MySQL连接
        self.connection = pymysql.connect(
            host=config.get('mysql', 'host'),  # 数据库主机地址
            port=int(config.get('mysql', 'port')),  # 数据库端口号，转换为整数
            user=config.get('mysql', 'user'),  # 数据库用户名
            password=config.get('mysql', 'password'),  # 数据库密码
            charset=config.get('mysql', 'charset'),  # 数据库字符集
        )
        # 创建数据库游标对象
        self.cursor = self.connection.cursor()
        # 从配置文件中获取需要管理的表列表
        # 格式为逗号分隔的字符串，分割后去除每个表名的首尾空格
        self.configured_tables = [
            t.strip() for t in config.get('mysql', 'tables').split(',')
        ]
        # 初始化DDL配置字典
        self.ddl_config = {}
        # 如果配置文件中包含'ddl'部分
        if config.has_section('ddl'):
            # 遍历'ddl'部分的所有选项（表名或default）
            for table in config.options('ddl'):
                # 将DDL语句添加到配置字典中
                self.ddl_config[table] = config.get('ddl', table)
        # 自动创建缺失的表
        self._create_missing_tables()

    def _create_missing_tables(self):
        """
        自动创建缺失的表（内部方法）
        流程:
        1. 获取数据库中已存在的表
        2. 找出配置中需要但数据库中不存在的表
        3. 为每个缺失的表执行DDL创建语句
        """
        # 获取数据库中已存在的表
        existing_tables = self._get_existing_tables()
        # 找出配置中需要但数据库中不存在的表
        missing_tables = [t for t in self.configured_tables if t not in existing_tables]
        # 遍历缺失的表并尝试创建
        for table in missing_tables:
            try:
                # 获取表的DDL创建语句
                ddl = self._get_table_ddl(table)
                # 执行DDL语句创建表
                self.cursor.execute(ddl)
                # 提交事务
                self.connection.commit()
            except Exception :
                # 静默处理所有异常（不输出错误信息）
                pass

    def _get_existing_tables(self):
        """
        获取数据库中已存在的表（内部方法）
        返回:
            数据库中存在的表名列表
        """
        # 执行SQL查询获取数据库中的所有表
        self.cursor.execute('SHOW TABLES')
        # 提取查询结果中的表名（每个结果是一个元组，取第一个元素）
        return [table[0] for table in self.cursor.fetchall()]

    def _get_table_ddl(self, table_name):
        """
        获取表的DDL创建语句（内部方法）
        优先级:
        1. 表特定DDL（如果配置中存在）
        2. 默认DDL（使用表名替换占位符）

        参数:
            table_name: 需要创建的表名

        返回:
            表的DDL创建语句
        """
        # 如果配置中有该表的特定DDL
        if table_name in self.ddl_config:
            return self.ddl_config[table_name]
        else:
            # 使用默认DDL，并将{table_name}替换为实际表名
            return self.ddl_config['default'].format(table_name=table_name)