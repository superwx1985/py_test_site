import os
import json
import datetime
import threading
import logging
import oracledb
import pymysql
from py_test.vic_tools import vic_find_object


# 使fetch操作返回字典
def makedict(cursor):
    cols = [d[0] for d in cursor.description]

    def createrow(*args):
        return dict(zip(cols, args))
    return createrow


# 获取查询结果
def get_sql_result(vic_step):
    select_result = list()
    if vic_step.db_type == 'oracle':
        pass
        # if vic_step.db_lang:
        #     os.environ['NLS_LANG'] = vic_step.db_lang
        # database_connect_string = '{}:{}/{}'.format(vic_step.db_host, vic_step.db_port, vic_step.db_name)
        # with cx_Oracle.connect(vic_step.db_user, vic_step.db_password, database_connect_string) as conn:
        #     timer = threading.Timer(vic_step.timeout, conn.cancel)
        #     cursor = conn.cursor()
        #     # 启动定时器，到达超时值后执行conn.cancel
        #     timer.start()
        #     raw_result = cursor.execute(vic_step.db_sql)
        #     # 如果是查询操作，cursor.description不为空
        #     if cursor.description:
        #         cursor.rowfactory = makedict(cursor)
        #         select_result = raw_result.fetchall()
        #         sql_result = '查询到{}条数据'.format(cursor.rowcount)
        #     else:
        #         sql_result = '影响行数{}'.format(cursor.rowcount)
        #     # 关闭定时器
        #     timer.cancel()
        #     cursor.close()
    elif vic_step.db_type == 'mysql':
        if vic_step.db_lang:
            charset = vic_step.db_lang
        else:
            charset = ''
        if isinstance(vic_step.db_port, str) and vic_step.db_port.isdigit():
            port = int(vic_step.db_port)
        else:
            port = 3306
        with pymysql.connect(host=vic_step.db_host, user=vic_step.db_user, password=vic_step.db_password,
                             database=vic_step.db_name, port=port, cursorclass=pymysql.cursors.DictCursor,
                             charset=charset, connect_timeout=vic_step.timeout) as cursor:
            cursor.execute(vic_step.db_sql)
            # 如果是查询操作，cursor.description不为空
            if cursor.description:
                select_result = cursor.fetchall()
                sql_result = '查询到{}行数据'.format(cursor.rowcount)
            else:
                sql_result = '影响行数{}'.format(cursor.rowcount)
    else:
        raise ValueError('不支持的数据库类型')
    return sql_result, select_result


# json dump操作时处理datetime对象
class JsonDatetimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S.%f')
        if isinstance(o, datetime.date):
            return o.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, o)


# 验证查询结果
def verify_db_test_result(expect, result, logger=logging.getLogger('py_test')):
    find_result = vic_find_object.find_with_condition(expect, result, logger=logger)
    if find_result.is_matched:
        run_result = ['p', find_result]
    else:
        run_result = ['f', find_result]
    return run_result


if __name__ == "__main__":
    import logging

    class VicStep:
        def __init__(self):
            self.db_type = 1
            self.db_lang = 'simplified chinese_china.UTF8'
            self.db_host = '192.192.189.193'
            self.db_port = 1521
            self.db_name = 'tdr'
            self.db_user = 'dw'
            self.db_password = 'dw'
            self.timeout = 50
            self.db_sql = 'select CI_ADDRESS from TB_B_C_CI WHERE ROWNUM <= 1'

            # logger = logging.getLogger()
            # handler = logging.StreamHandler()
            # logger.addHandler(handler)
            # logger.setLevel(10)
            # self.logger = logger


    vs = VicStep()
    a, b = get_sql_result(vs)

    print(a)
    print(type(b), b)
