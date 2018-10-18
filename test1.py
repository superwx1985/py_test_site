


from sys import argv
import argparse

parser = argparse.ArgumentParser(description='py_test命令行客户端')
parser.add_argument(
    "-s",
    "--server",
    help="测试服务器地址",
    default=None,
    required=True,
)
parser.add_argument(
    "-i",
    "--id",
    dest="suite_id",
    help="测试套件ID",
    default=None,
    required=True,
)
parser.add_argument(
    "-t",
    "--token",
    help="授权token",
    default=None,
    required=True,
)
parser.add_argument(
    "-o",
    "--timeout",
    type=int,
    help="客户端超时设置（秒）",
    default=300,
)
parser.add_argument(
    "-l",
    "--level",
    type=int,
    help="客户端日志级别（1=DEBUG，2=INFO，3=WARNING，4=ERROR，5=CRITICAL）",
    choices=[1, 2, 3, 4, 5],
    default=2,
)

args = parser.parse_args(argv[1:])

print(args)

