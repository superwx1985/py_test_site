from ftplib import FTP
import ftplib
import os,sys,string,datetime,time
import socket
class MYFTP:
    def __init__(self, hostaddr, username, password, remotedir, port=21, encoding='utf-8'):
        self.hostaddr = hostaddr
        self.username = username
        self.password = password
        self.encoding = encoding
        self.remotedir  = remotedir
        self.port     = port
        self.ftp      = FTP()
        self.file_list = []
        self.level = 0
        # self.ftp.set_debuglevel(2) #显示FTP详细调试信息

    def __del__(self):
        self.ftp.close()
        # self.ftp.set_debuglevel(0)

    def login(self):
        ftp = self.ftp
        timeout = 60
        socket.setdefaulttimeout(timeout)
        ftp.set_pasv(True)
        ftp.encoding = self.encoding #设置字符编码
        print ('开始连接到 %s:%s' %(self.hostaddr,self.port))
        ftp.connect(self.hostaddr, self.port)
        ftp.login(self.username, self.password)
        debug_print(ftp.getwelcome())
        ftp.cwd(self.remotedir)

    def is_same_size(self, localfile, remotefile):
        try:
            remotefile_size = self.ftp.size(remotefile)
        except:
            remotefile_size = -1
        try:
            localfile_size = os.path.getsize(localfile)
        except:
            localfile_size = -1
        debug_print('lo:%d  re:%d' %(localfile_size, remotefile_size),)
        if remotefile_size == localfile_size:
            return 1
        else:
            return 0

    def download_file(self, localfile, remotefile):
        if self.is_same_size(localfile, remotefile):
            print('【%s】文件大小相同，跳过' %localfile)
            return
        else:
            print('【%s】>>>>>>>>>>>>下载中 ...' %localfile)
        #return
        file_handler = open(localfile, 'wb')
        self.ftp.retrbinary('RETR %s'%(remotefile), file_handler.write)
        file_handler.close()

    def download_files(self, localdir='.\\', remotedir='./', level=0):
        try:
            self.ftp.cwd(remotedir)
        except:
            debug_print('【%s】不存在，继续...' %remotedir)
            return
        if not os.path.isdir(localdir):
            os.makedirs(localdir)
            print('为【%s】创建本地目录'  %(self.ftp.pwd()))
        else:
            if self.level > 0:
                print('【%s】的本地目录已存在，无需创建'  %(self.ftp.pwd()))     
        debug_print('切换至目录【 %s】' %self.ftp.pwd())
        self.file_list = []
        self.get_file_list()
        #self.ftp.dir(self.get_file_list)
        remotenames = self.file_list
        debug_print(remotenames)
        for item in remotenames:
            file_type = item[0]
            file_name = item[1]
            local = os.path.join(localdir, file_name)
            if file_type == 'd':
                self.level += 1
                self.download_files(local, file_name, self.level)
            elif file_type == '-':
                self.download_file(local, file_name)
        self.level -= 1
        if self.level >= 0:
            self.ftp.cwd('..')
            print('返回上层目录【 %s】' %self.ftp.pwd())

    def upload_file(self, localfile, remotefile):
        if not os.path.isfile(localfile):
            return
        if self.is_same_size(localfile, remotefile):
            print('【%s】文件大小相同，跳过' %localfile)
            return
        file_handler = open(localfile, 'rb')
        self.ftp.storbinary('STOR %s' %remotefile, file_handler)
        file_handler.close()
        print('【%s】已传送' %localfile)

    def upload_files(self, localdir='.\\', remotedir = './', mkdir=False):
        if not os.path.isdir(localdir):
            return
        self.ftp.cwd(remotedir)
        if mkdir:
            try:
                self.ftp.mkd(os.path.split(localdir)[1])
                print('为【%s】创建远程目录'  %(localdir))
            except ftplib.error_perm as e:
                if '550 Cannot create a file when that file already exists.' in str(e): 
                    print('【%s】的远程目录已存在，无需创建' %(localdir))
                else:
                    raise
            except:
                raise
            self.ftp.cwd(os.path.split(localdir)[1])
        localnames = os.listdir(localdir)
        for item in localnames:
            src = os.path.join(localdir, item)
            if os.path.isdir(src):
                try:
                    self.ftp.mkd(item)
                    print('为【%s】创建远程目录'  %(localdir+'\\'+item))
                except ftplib.error_perm as e:
                    if '550 Cannot create a file when that file already exists.' in str(e): 
                        print('【%s】的远程目录已存在，无需创建' %(localdir+'\\'+item))
                    else:
                        raise
                except:
                    raise
                self.upload_files(src, item)
            else:
                self.upload_file(src, item)
        self.ftp.cwd('..')

    def get_file_list(self):
        file_list = self.ftp.nlst()
        file_type = 'd'
        for x in file_list:
            try:
                self.ftp.cwd(x)
                self.ftp.cwd('..')
            except ftplib.error_perm as e:
                if '550 The filename, directory name, or volume label syntax is incorrect.' in str(e):
                    file_type = '-'
                else:
                    raise
            except:
                raise
            self.file_list.append((file_type, x))
        
def debug_print(s, debug_=0):
    if debug_:
        print (s)

#===============================================================================
# def deal_error(e):
#     timenow  = time.localtime()
#     datenow  = time.strftime('%Y-%m-%d', timenow)
#     logstr = '%s 发生错误: %s' %(datenow, e)
#     debug_print(logstr)
#     file.write(logstr)
#     sys.exit()
#===============================================================================

if __name__ == '__main__':
    #file = open("d:\\test\\log.txt", "a")
    #timenow  = time.localtime()
    #datenow  = time.strftime('%Y-%m-%d %H:%M:%S', timenow)
    #logstr = datenow
    # 配置如下变量
    hostaddr = '192.168.119.23' # ftp地址
    username = 'wangx' # 用户名
    password = '123456' # 密码
    port  =  9921 # 端口号
    encoding = 'gbk' #设置字符编码
    rootdir_local  = 'D:\\vic_test_result\\Automation_Test_Report_2016-12-05_134814'#'d:\\ftp_bak\\' # 本地目录
    rootdir_remote = '/'          # 远程目录
    f = MYFTP(hostaddr, username, password, rootdir_remote, port, encoding)
    f.login()
    #f.download_files(rootdir_local, rootdir_remote)
    f.upload_files(rootdir_local, rootdir_remote, 1)
    #timenow  = time.localtime()
    #datenow  = time.strftime('%Y-%m-%d %H:%M:%S', timenow)
    #logstr += " - %s 成功执行了备份\n" %datenow
    #file.write(logstr)
    #file.close()