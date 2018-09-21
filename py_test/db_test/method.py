import cx_Oracle
import os
import logging
import json
import datetime
from py_test.vic_tools import vic_find_object


# 使fetch操作返回字典
def makedict(cursor):
    cols = [d[0] for d in cursor.description]

    def createrow(*args):
        return dict(zip(cols, args))
    return createrow


# 获取查询结果
def get_sql_result(db_type, db_host, db_port, db_name, db_user, db_password, sql):
    if db_type == 1:
        os.environ['NLS_LANG'] = 'simplified chinese_china.UTF8'
        database_connect_string = '{}:{}/{}'.format(db_host, db_port, db_name)
        with cx_Oracle.connect(db_user, db_password, database_connect_string) as conn:
            cursor = conn.cursor()
            raw_result = cursor.execute(sql)
            cursor.rowfactory = makedict(cursor)
            sql_result = raw_result.fetchall()
            cursor.close()
    else:
        raise ValueError('目前只支持oracle数据库')
    return sql_result


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
def verify_sql_result(expect, sql_result):
    find_result = vic_find_object.find_with_condition(expect, sql_result)
    if find_result.is_matched:
        run_result = ('p', find_result)
    else:
        run_result = ('f', find_result)
    return run_result
