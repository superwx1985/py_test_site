#!/usr/bin/env python
import os
import sys


# 获取工程根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# 日志目录
LOG_DIR = os.path.join(PROJECT_ROOT, 'log')
# 检查日志目录是否存在
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
    print('***** 创建日志文件夹 [%s] *****' % LOG_DIR)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "py_test_site.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)
