README
===========================

Vic的自动化测试网站
****

# 部署
PS: 下述内容涉及到的命令都应在项目路径下执行

## 下载项目
下载并解压到本地路径

## 安装python
本项目使用的python版本为3.12

## 安装依赖包

### 通过pip安装大部分依赖包
```
pip install -r requirements.txt
```

### 需要特殊安装的依赖包
```
pip install "psycopg[binary]"
```

## 安装并配置Nginx
配置文件请参考 other/deploy/nginx.conf

## 启动Nginx
### Windows
```
#启动
start nginx
#关闭
nginx -s stop
#重启
nginx -s reload
```
### Linux
```
#启动
./nginx
#关闭
./nginx -s stop
#重启
./nginx -s reload
```
## 配置Redis
修改py_test_site/settings.py中的CHANNEL_LAYERS参数。如只使用debug模式运行，无需单独配置。实际部署时建议使用Redis。

## 配置数据库
### 使用自带的sqlite3数据库
确保配置文件py_test_site/settings.py中的sqlite3数据库配置未被注释

### 使用其他数据库
#### 从sqlite3导出基础数据
```
python -Xutf8 manage.py dumpdata -e main.caseresult -e main.stepresult -e main.suiteresult -e main.image -e contenttypes -o db_data.json
```
参考： https://docs.djangoproject.com/en/5.0/ref/django-admin/#:~:text=dumpdata

#### 在配置中启用其他数据库
修改py_test_site/settings.py，注释sqlite3数据库配置，根据实际情况填写并启用其他数据库的配置  
PS: 请确保其他数据库已启动，并且访问权限已正确配置

#### 创建表结构
'''
python manage.py makemigrations
python manage.py migrate
'''

#### 导入基础数据
```
python -Xutf8 manage.py loaddata db_data.json
```
## 创建静态文件目录
```
python manage.py collectstatic
```
## 启动项目
```
python other\vic_daphne_server.py py_test_site.asgi:application -p 8001
```

## 访问网站
http://127.0.0.1:80/user/login/  
```
管理员账号：admin/abcd123!
QA1：vic/123456
QA2：vic2/123456
QA Lead：vic_admin/123456
```