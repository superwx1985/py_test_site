import cx_Oracle
import logging


logger = logging.getLogger('py_test')


# 获取查询结果
def get_sql_result(database_type, database_host, database_port, database_name, user, password, sql):
    if database_type.lower() == 'oracle':
        database_connect_string = '%s:%s/%s' % (database_host, database_port, database_name)
        conn = cx_Oracle.connect(user, password, database_connect_string)
        cursor = conn.cursor()
        raw_result = cursor.execute(sql)
        sql_result = raw_result.fetchall()
        cursor.close()
        conn.close()
    else:
        raise ValueError('目前只支持oracle数据库')
    return sql_result


# 验证查询结果
def verify_sql_result(expect, sql_result):
    i = -1
    for line in sql_result:
        i += 1
        sql_result[i] = list(line)
    from py_test.vic_tools import vic_find_object
    find_result = vic_find_object.find_with_condition(expect, sql_result)
    from json import dumps
    pretty_result = dumps(sql_result, indent=1, ensure_ascii=False)
    if find_result.is_matched:
        run_result = ('p', 'PASS\n' + 'Result:\n' + pretty_result)
    else:
        run_result = ('f', 'FAIL\n' + 'Result:\n' + pretty_result)
    logger.debug(run_result[1])
    return run_result
