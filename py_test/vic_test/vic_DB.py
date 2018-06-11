#===============================================================================
# import pymssql#连接MSSQL（用数据库用户）
#  
# conn = pymssql.connect(host='GZ-VICWANG\MSSQLSERVER11',user='sa',password ='sa',database='test')
# cur=conn.cursor()
# cur.execute('SELECT TOP 100 * FROM cdsgus')
# print(cur.fetchone()[0])
# conn.close()
#===============================================================================

#===============================================================================
# import pyodbc#连接MSSQL（用windows用户登录）
# server='qadb01'
# database='KnotCommerce'
# user=''
# pwd=''
# trusted='yes'#用windows用户登录
# conn_str = 'Driver={SQL Server};Server=%s;Database=%s;UID=%s;PWD=%s;Trusted_Connection=%s;'%(server, database, user, pwd, trusted)
# sql_str = "SELECT top 10 * FROM [dbo].[CatalogEntry]"
# connect = pyodbc.connect(conn_str)
# cursor = connect.cursor()
# cursor.execute(sql_str)
# #result = cursor.fetchall()
# #print(result)
# #===============================================================================
# # while 1:
# #     row = cursor.fetchone()
# #     if not row:
# #         break
# #     print (row.Name)
# #===============================================================================
# row_description = cursor.description
# result = []
# for row_value in cursor.fetchall():
#     row = []
#     for column in range(len(row_description)):
#         row.append((column+1,row_description[column][0],row_value[column]))
#     result.append(row)
# connect.close()
# for i in result:
#     print(i)
#===============================================================================


import pymysql#连接mysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='', db='mysql',charset='utf8')#要支持中文请加入charset='utf8'
cur = conn.cursor()
cur.execute("SELECT Host,User,Password FROM user")
print(cur.description)#显示表的字段信息
 
for r in cur.fetchall():
    print(r)
cur.close()
conn.close()

with pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='', db='mysql',charset='utf8') as cur:
    cur.execute("SELECT Host,User,Password FROM user")
    print(cur.description)
    for r in cur.fetchall():
        print(r)











