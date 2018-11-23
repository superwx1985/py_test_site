import os
import json
import datetime
import threading
import logging
import cx_Oracle
import pymysql
from py_test.vic_tools import vic_find_object


# 使fetch操作返回字典
def makedict(cursor):
    cols = [d[0] for d in cursor.description]

    def createrow(*args):
        return dict(zip(cols, args))
    return createrow


# 获取查询结果
def get_sql_result(
        db_type, db_host, db_port, db_name, db_user, db_password, db_lang, sql, timeout=10):
    select_result = list()
    if db_type == 1:
        if db_lang:
            os.environ['NLS_LANG'] = db_lang
        database_connect_string = '{}:{}/{}'.format(db_host, db_port, db_name)
        with cx_Oracle.connect(db_user, db_password, database_connect_string) as conn:
            timer = threading.Timer(timeout, conn.cancel)
            cursor = conn.cursor()
            # 启动定时器，到达超时值后执行conn.cancel
            timer.start()
            raw_result = cursor.execute(sql)
            # 如果是查询操作，cursor.description不为空
            if cursor.description:
                cursor.rowfactory = makedict(cursor)
                select_result = raw_result.fetchall()
                sql_result = '查询到{}行数据'.format(cursor.rowcount)
            else:
                sql_result = '影响行数{}'.format(cursor.rowcount)
            # 关闭定时器
            timer.cancel()
            cursor.close()
    elif db_type == 2:
        if db_lang:
            charset = db_lang
        else:
            charset = ''
        if isinstance(db_port, str) and db_port.isdigit():
            port = int(db_port)
        else:
            port = 3306
        with pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_name, port=port,
                             cursorclass=pymysql.cursors.DictCursor, charset=charset,
                             connect_timeout=timeout) as cursor:
            cursor.execute(sql)
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
def verify_sql_result(expect, sql_result, logger=logging.getLogger('py_test')):
    find_result = vic_find_object.find_with_condition(expect, sql_result, logger=logger)
    if find_result.is_matched:
        run_result = ['p', find_result]
    else:
        run_result = ['f', find_result]
    return run_result
