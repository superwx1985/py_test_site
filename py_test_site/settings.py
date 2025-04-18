import os
import sys
from django.urls import reverse_lazy
from manage import PROJECT_ROOT
from py_test_site.version import SITE_VERSION
import psycopg

# 站点名称
SITE_NAME = '自动化测试平台'

# 最大并行测试线程数
SUITE_MAX_CONCURRENT_EXECUTE_COUNT = 8

# 步骤循环次数限制
LOOP_ITERATIONS_LIMIT = 100

# 出错后暂停的最大时间（秒）
ERROR_PAUSE_TIMEOUT = 600

# 服务器本地浏览器及驱动位置
CHROME_BINARY_LOCATION = "D:/vic/selenium/chrome-win64/chrome.exe"
WEBDRIVER_CHROME_DRIVER = "D:/vic/selenium/chromedriver-win64/chromedriver.exe"

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
DEBUG = True

# 在 Django 中关闭 X-Frame-Options: DENY
X_FRAME_OPTIONS = 'SAMEORIGIN'
# 显式指定自增主键的类型
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    "daphne",
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
            os.path.join(BASE_DIR, 'templates'),
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
# Channels
# ASGI_APPLICATION = 'py_test_site.routing.application'
ASGI_APPLICATION = 'py_test_site.asgi.application'


def get_database_settings(database) -> dict:
    _DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'debug_db/db.sqlite3'),
        }
    }
    if database == "sqlite3":
        pass
    elif database == "mysql":
        import pymysql
        pymysql.install_as_MySQLdb()  # mysql改用pymysql驱动

        _DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'py_test_site',
                # 'HOST': '127.0.0.1',
                'HOST': '10.0.16.144',
                'PORT': '3306',
                'USER': 'py_test_site',
                'PASSWORD': 'py_test_site',
                # 'HOST': '52.82.80.187',
                # 'PORT': '3306',
                # 'USER': 'root',
                # 'PASSWORD': 'Pass@word1',
            }
        }
    elif database == "postgresql":
        _DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "py_test_site",
                "USER": "postgres",
                "PASSWORD": "admin",
                "HOST": '',
                "PORT": 5432,
            }
        }
    else:
        print(f"Cannot found the setting of {database}, use sqlite3 instead")

    return _DATABASES


# 数据库迁移 https://docs.djangoproject.com/zh-hans/5.0/topics/migrations/
databases = {1: "sqlite3", 2: "mysql", 3: "postgresql"}
DATABASES = get_database_settings(databases[2])

# 数据库保持连接（秒），0-每次请求结束时关闭数据库连接，None-无限制的持久连接
CONN_MAX_AGE = 60

# 用户密码复杂度校验规则
# UserAttributeSimilarityValidator 检查密码和一组用户属性集合之间的相似性。
# MinimumLengthValidator 用来检查密码是否符合最小长度。这个验证器可以自定义设置长度，默认8个字符。
# CommonPasswordValidator 检查密码是否在常用密码列表中。默认情况下，它会与列表中的2000个常用密码作比较。
# NumericPasswordValidator 检查密码是否是完全是数字的。
AUTH_PASSWORD_VALIDATORS = [
    # {
    #     "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    #     "OPTIONS": {
    #         "min_length": 9,
    #     },
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    # },
]

# Internationalization

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = False

# Django Admin 时间格式化
DATETIME_FORMAT = 'Y-m-d H:i:s'
DATE_FORMAT = 'Y-m-d'

# 使用时区
USE_TZ = False

# 静态文件地址
STATIC_URL = '/static/'

# 当执行manage collectstatic时，静态文件的集中存放路径
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

# 项目公用静态文件的路径
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'common_static/'),
]

# 静态文件查找顺序，默认先找STATICFILES_DIRS中的，然后找各应用的，找到则停止
# STATICFILES_FINDERS = [
#     'django.contrib.staticfiles.finders.FileSystemFinder',
#     'django.contrib.staticfiles.finders.AppDirectoriesFinder',
# ]

# 媒体文件地址
MEDIA_URL = '/media/'

# 默认上传路径
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
        'websocket': {
            'format': '%(asctime)s - %(message)s',
            'datefmt': '%H:%M:%S',
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
            'when': 'D',  # 时间间隔单位
            'interval': 1,  # 时间间隔值
            'backupCount': 30,  # 保留日志数量
            'formatter': 'standard',  # 使用哪种formatters日志格式
            'encoding': 'utf-8',  # 使用utf-8编码
        },
        # # 服务器错误日志文件
        # 'server_error': {
        #     'level': 'ERROR',
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'filename': os.path.join(LOG_DIR, 'server_error.log'),
        #     'maxBytes': 1024*1024*10,
        #     'backupCount': 10,
        #     'formatter': 'detail',
        # },
        # # 邮件通知
        # 'mail_admins': {
        #     'level': 'ERROR',
        #     'class': 'django.utils.log.AdminEmailHandler',
        #     'include_html': True,
        # },
        # # 请求日志文件
        # 'server_request': {
        #     'level': 'DEBUG',
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'filename': os.path.join(LOG_DIR, 'server_request.log'),
        #     'maxBytes': 1024*1024*10,
        #     'backupCount': 3,
        #     'formatter': 'standard',
        # },
        # # sql日志文件
        # 'server_sql': {
        #     'level': 'DEBUG',
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'filename': os.path.join(LOG_DIR, 'server_sql.log'),
        #     'maxBytes': 1024*1024*100,
        #     'backupCount': 3,
        #     'formatter': 'standard',
        # },
        # 测试执行日志文件
        'py_test': {
            'level': log_level,
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'py_test.log'),
            'when': 'D',
            'interval': 1,
            'backupCount': 30,
            'formatter': 'detail',
            'encoding': 'utf-8',
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
            'propagate': False,  # 日志记录只由当前 logger 处理，不会向上传递
        },
        # 请求日志
        'django.request': {
            'handlers': ['server', 'console_normal', 'console_warning'],
            'level': log_level,
            'propagate': False,
        },
        # sql日志
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
        # daphne日志
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

# 设置channel使用的通道层
if DEBUG:
    # 调试时使用内置的Channel Layer
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
else:
    # 正式部署时建议使用Redis
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                # "hosts": ["redis://:{密码}@{地址}:{端口}/{数据库编号}"],
                "hosts": ["redis://:123456@localhost:6379/1"],
                "symmetric_encryption_keys": [SECRET_KEY],
            },
        },
    }

# GLB专用配置
GLB = {"GTM_BASE_URL": "https://gtm.greenworkstools.com.cn:991"}
