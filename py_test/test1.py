import os


# 获取工程根目录
project_dir = os.path.dirname(os.path.abspath(__file__))
# 日志目录
log_dir = os.path.join(project_dir, 'log')

print(project_dir)
print(log_dir)