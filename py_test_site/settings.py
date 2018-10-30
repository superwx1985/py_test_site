import os
import sys
from django.urls import reverse_lazy
from manage import PROJECT_ROOT


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 日志目录
LOG_DIR = os.path.join(PROJECT_ROOT, '../py_test_site_log/')
# 检查日志目录是否存在
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
    print('***** 创建日志文件夹 [{}] *****'.format(os.path.abspath(LOG_DIR)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '-8=0r94)m^&x^v7)886@@&iq$2aa*#8@d)dji+x)o(5l1a4dui'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'channels',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'widget_tweaks',

    'main',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'py_test_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'py_test_site.wsgi.application'

# sqlite3 数据库

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'debug_db/db.sqlite3'),
#     }
# }

# mysql 数据库

import pymysql
pymysql.install_as_MySQLdb()  # mysql改用pymysql驱动

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'py_test_site',
        'HOST': '127.0.0.1',
        # 'HOST': '192.192.185.140',
        'PORT': '3306',
        'USER': 'py_test_site',
        'PASSWORD': 'py_test_site',
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]


# Internationalization

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

# USE_L10N = True

# Django Admin 时间格式化
USE_L10N = False
DATETIME_FORMAT = 'Y-m-d H:i:s'
DATE_FORMAT = 'Y-m-d'

# 使用时区
USE_TZ = False


# Static files (CSS, JavaScript, Images)

# 静态文件地址
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

# 媒体文件地址
MEDIA_URL = '/media/'

# 默认上传位置

MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# 登陆页面
LOGIN_URL = reverse_lazy('user_login')


# 日志配置
log_level = 'DEBUG' if DEBUG else 'INFO'  # 如果DEBUG打开则启动DEBUG日志

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    # 日志格式
    'formatters': {
       'standard': {
            'format': '%(asctime)s [%(threadName)s] [%(name)s] [%(module)s:%(funcName)s:%(lineno)d] [%(levelname)s] - %(message)s'
       },
       'detail': {
            'format': '%(asctime)s [%(threadName)s:%(thread)d] [%(name)s] [%(pathname)s:%(funcName)s:%(lineno)d] [%(levelname)s] - %(message)s'
       },
    },
    # 过滤器
    'filters': {
        'non_warning_filter': {
            '()': 'utils.log.NonWarningFilter'
        }
    },
    # 处理器
    'handlers': {
        # 控制台打印正常日志
        'console_normal': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': sys.stdout,
            'filters': ['non_warning_filter'],
        },
        # 控制台打印警告及错误日志
        'console_warning': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': sys.stderr,
        },
        # 服务器日志文件
        'server': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'server.log'),  # 日志输出文件
            'when': 'D',                # 时间间隔单位
            'interval': 1,              # 时间间隔值
            'backupCount': 30,          # 保留日志数量
            'formatter': 'detail',    # 使用哪种formatters日志格式
        },
        # 服务器错误日志文件
        # 'server_error': {
        #     'level': 'ERROR',
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'filename': os.path.join(LOG_DIR, 'server_error.log'),
        #     'maxBytes': 1024*1024*10,
        #     'backupCount': 10,
        #     'formatter': 'detail',
        # },
        # 邮件通知
        # 'mail_admins': {
        #     'level': 'ERROR',
        #     'class': 'django.utils.log.AdminEmailHandler',
        #     'include_html': True,
        # },
        # 请求日志文件
        # 'server_request': {
        #     'level': 'DEBUG',
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'filename': os.path.join(LOG_DIR, 'server_request.log'),
        #     'maxBytes': 1024*1024*10,
        #     'backupCount': 3,
        #     'formatter': 'standard',
        # },
        # sql日志文件
        # 'server_sql': {
        #     'level': 'DEBUG',
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'filename': os.path.join(LOG_DIR, 'server_sql.log'),
        #     'maxBytes': 1024*1024*10,
        #     'backupCount': 3,
        #     'formatter': 'standard',
        # },
        # 测试执行日志文件
        'py_test': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'py_test.log'),
            'when': 'D',
            'interval': 1,
            'backupCount': 30,
            'formatter': 'detail',
        },
        # 测试执行错误日志文件
        # 'py_test_error': {
        #     'level': 'ERROR',
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'filename': os.path.join(LOG_DIR, 'py_test_error.log'),
        #     'maxBytes': 1024*1024*10,
        #     'backupCount': 10,
        #     'formatter': 'detail',
        # },
    },
    'loggers': {
        # django主日志
        'django': {
            'handlers': ['server', 'console_normal', 'console_warning'],
            'level': log_level,
            'propagate': False,
        },
        # # 请求日志
        # 'django.request': {
        #     'handlers': ['server_request'],
        #     'level': log_level,
        # },
        # # sql日志
        # 'django.db.backends': {
        #     'handlers': ['server_sql'],
        #     'level': log_level,
        # },
        # 模板日志，模板debug内容太多，此处固定为INFO级别
        'django.template': {
            'level': 'INFO',
        },
        # channels日志
        # 'django.channels': {
        #     'level': log_level,
        # },
        # daphne服务日志
        'daphne': {
            'handlers': ['server', 'console_normal', 'console_warning'],
            'level': log_level,
            'propagate': False,
        },
        # 测试执行日志，此为顶层日志，应固定为DEBUG级别，每次测试的具体日志级别由测试套件指定
        'py_test': {
            'handlers': ['py_test', 'console_normal', 'console_warning'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Channels
ASGI_APPLICATION = 'py_test_site.routing.application'

# 站点名称
SITE_NAME = '汇智自动化测试工具'

# 站点版本
SITE_VERSION = 'V1.5.20181030.01'

