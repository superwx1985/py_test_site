import pymysql

sql = 'select code, name, created_date  from main_action where code in ("UI_GO_TO_URL", "DB_EXECUTE_SQL")'
# sql = 'update main_suiteresult set name="test2" where id=1005'
sql = 'delete from main_stepresult where id=11278'
sql_result = None


conn = pymysql.connect(host='127.0.0.1', user='root', password='root', database='py_test_site', port=3306, cursorclass=pymysql.cursors.DictCursor)

c = conn.cursor()
a = c.execute(sql)
conn.commit()
sql_result = c.fetchall()


print(sql_result)


# import cx_Oracle
# import os
#
#
# os.environ['NLS_LANG'] = 'simplified chinese_china.UTF8'
#
# db_host = '192.192.189.193'
# db_port = 1521
# db_name = 'tdr'
# db_user = 'dw'
# db_password = 'dw'
# sql = 'select CI_ADDRESS, CREATE_DATE, CI_NAME_CH from TB_B_C_CI WHERE ROWNUM <= 3'
# # sql = 'update TB_B_C_CI set AREA_NAME = 1 where ROWNUM = 1'
#
# database_connect_string = '{}:{}/{}'.format(db_host, db_port, db_name)
# with cx_Oracle.connect(db_user, db_password, database_connect_string) as conn:
#     cursor = conn.cursor()
#     raw_result = cursor.execute(sql)
#     select_result = raw_result.fetchall()
#     cursor.close()
