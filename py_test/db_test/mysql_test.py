import pymysql


def execute_sql_query(host: str, port: int, user: str, password: str, database: str, charset: str, sql: str) -> dict:
    """
    执行 SQL 查询并返回结果
    Args:
        host: 数据库主机地址
        port: 数据库端口
        user: 数据库用户名
        password: 数据库密码
        database: 数据库名称
        charset: 数据库字符集
        sql: 要执行的 SQL 查询语句
    """
    sql_result = {"count": 0, "desc": None, "result": None}
    try:
        # 建立数据库连接
        with pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset=charset,
            cursorclass=pymysql.cursors.DictCursor  # 返回字典格式数据（可选）
        ) as connection:
            # 创建游标对象
            with connection.cursor() as cursor:
                # 执行 SQL 查询
                cursor.execute(sql)
                # 获取查询结果
                sql_result["count"] = cursor.rowcount

                # 提交事务
                if cursor.description:  # 如果是查询操作，cursor.description不为空
                    sql_result["desc"] = cursor.description
                    sql_result["result"] = cursor.fetchall()
                else:
                    connection.commit()
                return sql_result

    except pymysql.Error as e:
        print(f"数据库操作失败: {e}")
        return sql_result
