# -*- coding: utf-8 -*-
import smtplib, time, os, mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage


def get_report(result_dir='D:\\vic_test_data\\KWS_test\\'):
    lists = os.listdir(result_dir)
    lists.sort(key=lambda x: os.path.getmtime(result_dir+x), reverse=True)
    reports = []
    i = 0
    for file in lists[1:]:
        if file[file.rfind('.')+1:] == 'html':
            break
        reports.append((result_dir+file,file))
        i += 1
    reports.append((result_dir+lists[0],lists[0]))
    return reports

 
def send_report(result_dir='D:\\vic_test_data\\KWS_test\\'):
    # 发送邮箱
    sender = '???@163.com'
    # 接收邮箱
    receiver = '???@126.com'
    # 发送邮件主题
    subject = get_report(result_dir)[-1][1]
    # 发送邮箱服务器
    smtpserver = 'smtp.163.com'
    # 发送邮箱用户/密码
    username = sender
    password = '???'
      
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = 'TKtester'
    msg['To'] = receiver
    msg['date'] = time.strftime('%Y-%m-%d %H:%M:%S:%z')
     
    msg.attach(MIMEText('KWS test report', _charset='utf-8'))
      
    reports = get_report(result_dir)[::-1]
  
    for file in reports:
           
        file_name = file[0]
        ctype, encoding = mimetypes.guess_type(file_name)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        att = MIMEImage((lambda f: (f.read(), f.close()))(open(file_name, 'rb'))[0], _subtype=subtype)
        att.add_header(
            'Content-Disposition', 'attachment', filename=file_name[file_name.rfind(result_dir)+len(result_dir):])
        msg.attach(att)
     
    smtp = smtplib.SMTP()
    smtp.connect(smtpserver)
    smtp.login(username, password)
    smtp.sendmail(sender, receiver, msg.as_string())
    smtp.quit()
    print('report has been sent to %s' % receiver)


if __name__ == '__main__':
    send_report('D:/vic_test_data/KWS_test/')
