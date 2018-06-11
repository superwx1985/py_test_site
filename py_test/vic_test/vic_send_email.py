# -*- coding: utf-8 -*-
import smtplib, time, mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# 发送邮箱
sender = 'vicwangtest@163.com'
# 接收邮箱
receiver = 'viwang@xogrp.com'
# 发送邮箱服务器
smtpserver = 'smtp.163.com'
# 发送邮箱用户/密码
username = 'vicwangtest@163.com'
password = 'abcd123!'
msg = MIMEMultipart()
# 发送邮件主题
msg['Subject'] = 'python email test'
msg['From'] = 'TKtester'
msg['To'] = receiver
msg['date'] = time.strftime('%Y-%m-%d %H:%M:%S:%z')
#添加邮件内容
msg.attach(MIMEText('<html><h1>你好！请查收附件。</h1></html>', _subtype='html', _charset='utf-8'))
#添加二进制附件 
fileName = r'D:\viwang\workspace\PyTest01\vic_test\csv1.csv'
ctype, encoding = mimetypes.guess_type(fileName)
if ctype is None or encoding is not None:
    ctype = 'application/octet-stream'
maintype, subtype = ctype.split('/', 1)
att = MIMEImage((lambda f: (f.read(), f.close()))(open(fileName, 'rb'))[0], _subtype = subtype)
att.add_header('Content-Disposition', 'attachment', filename = fileName)
msg.attach(att)
#继续添加二进制附件 
fileName = r'D:\viwang\workspace\PyTest01\vic_test\jpg 100x100.jpg'
ctype, encoding = mimetypes.guess_type(fileName)
if ctype is None or encoding is not None:
    ctype = 'application/octet-stream'
maintype, subtype = ctype.split('/', 1)
att = MIMEImage((lambda f: (f.read(), f.close()))(open(fileName, 'rb'))[0], _subtype = subtype)
att.add_header('Content-Disposition', 'attachment', filename = fileName)
msg.attach(att)


#实例化
#===============================================================================
# smtp = smtplib.SMTP()
# smtp.connect(smtpserver)
# smtp.login(username, password)
# smtp.sendmail(sender, receiver, msg.as_string())
# smtp.quit()
# print('email has sent to %s' % receiver)
#===============================================================================
