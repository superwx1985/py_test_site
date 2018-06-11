from py_test.general.run_case_group import batch_run_excel

case_type = 'ui'
case_dir = 'D:/vic/debug/Test Case/api'
case_prefix = '''
test_
'''
case_suffix = '''
xls, xlsx
'''
case_keyword = '''

'''
result_dir = 'D:/vic/Debug'

report_name = batch_run_excel(case_dir=case_dir, case_prefix=case_prefix, case_suffix=case_suffix,
                              case_keyword=case_keyword, result_dir=result_dir, case_type=case_type, base_timeout=30,
                              report_title='自动化测试报告', print_=1, get_ss=0, debug=1)

# 报告上传ftp
# import os
# import vic_test.vic_FTP as vic_FTP
# hostaddr = '192.168.119.23' # ftp地址
# username = 'wangx' # 用户名
# password = '123456' # 密码
# port  =  9921 # 端口号
# encoding = 'gbk' #设置字符编码
# rootdir_remote = '/' # 远程目录
# rootdir_local  = os.path.split(report_name)[0] # 本地目录
# f = vic_FTP.MYFTP(hostaddr, username, password, rootdir_remote, port, encoding)
# f.login()
# f.download_files(rootdir_local, rootdir_remote)
# f.upload_files(rootdir_local, rootdir_remote, 1)
