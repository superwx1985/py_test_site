#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    # 获取工程根目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    # 日志目录
    log_dir = os.path.join(project_dir, 'log')
    # 检查日志目录是否存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print('***** 创建日志文件夹 [%s] *****' % log_dir)
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
