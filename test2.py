import re
import datetime


file_path = '''
D:/vic/性能测试数据/sqs_log/sqs.log
'''
time_reg = '\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}'
start_time_str = '2018-05-10 16:20:00'
end_time_str = '2018-05-10 16:21:30'


class LogObject:
    def __init__(self, obj):
        self.obj = obj
        self.sorted_list = sorted(self.obj.items(), key=lambda x: x[1])

    def get_count(self):
        return len(self.obj)

    def get_sum(self):
        sum_ = 0
        for x in self.obj.values():
            sum_ += x
        return sum_

    def get_avg(self):
        return self.get_sum()/self.get_count()

    def get_min(self):
        return self.sorted_list[0][1]

    def get_max(self):
        return self.sorted_list[-1][1]

    def get_percent(self, percent):
        return self.sorted_list[round(self.get_count() * percent / 100) - 1][1]


# 字符串转时间
def str_to_time(str_='now', time_format=''):
    str_ = str(str_).lower()
    time_ = None
    if str_ == 'now':
        time_ = datetime.datetime.now()
    elif time_format != '':
        try:
            time_ = datetime.datetime.strptime(str_, time_format)
        except ValueError:
            raise ValueError('无法转换【{}】为指定的时间格式【{}】'.format(str_, time_format))
    else:
        for time_format in (
                '%Y-%m-%d %H:%M:%S.%f', '%Y%m%d%H%M%S%f', '%Y-%m-%d %H:%M:%S', '%Y%m%d%H%M%S', '%Y-%m-%d', '%Y%m%d'):
            try:
                time_ = datetime.datetime.strptime(str_, time_format)
                break
            except ValueError:
                pass
        if time_ is None:
            raise ValueError('无法转换【{}】为常用的时间格式，请手动指定时间格式'.format(str_))
    return time_


analyse_start_time = datetime.datetime.now()
start_time = str_to_time(start_time_str, '%Y-%m-%d %H:%M:%S')
end_time = str_to_time(end_time_str, '%Y-%m-%d %H:%M:%S')
d = dict()
with open(file_path.strip(), mode='r', encoding='utf8') as f:
    i = 0
    start = False
    for line in f.readlines():
        i += 1
        if i % 10000 == 0:
            print('已读取{}行'.format(i))
        if 'L:155' in line:
            # print(line, end='')
            if not start:
                match_text = re.match(time_reg, line)
                if match_text:
                    line_time = str_to_time(match_text.group(0), '%Y-%m-%d %H:%M:%S')
                    if line_time >= start_time:
                        start = True
                        start_time = line_time
        if start:
            match_text = re.match(time_reg, line)
            if match_text:
                line_time = str_to_time(match_text.group(0), '%Y-%m-%d %H:%M:%S')
                if line_time > end_time:
                    end_time = line_time
                    # print(line, end='')
                    print('已读取{}行'.format(i))
                    break
            match_text = re.search('MatrixGate查询【(.*?)】耗时:【(\d+?)ms】', line)
            # match_text = re.search('MatrixGate\?\?\?(.*?)\?\?\?:\?(\d+?)ms\?', line)
            if match_text:
                task_id = match_text.group(1)
                escape_time = int(match_text.group(2))
                # print(task_id, escape_time)
                d[task_id] = escape_time


lo = LogObject(d)
print('\n==========\n分析了【{}】到【{}】之间的日志'.format(start_time, end_time))
print('分析耗时：{}秒'.format(datetime.datetime.now() - analyse_start_time))
# print(lo.sorted_list)
print('符合条件的时间日志条数：{}'.format(lo.get_count()))
print('平均时间：{}'.format(lo.get_avg()))
print('最小时间：{}'.format(lo.get_min()))
print('最大时间：{}'.format(lo.get_max()))
# print(lo.get_percent(90))
