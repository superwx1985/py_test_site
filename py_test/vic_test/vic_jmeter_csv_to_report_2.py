import csv, datetime, os, time
from sys import argv

def timestamp_to_time(timestamp=time.time()):#时间戳转时间
    time_ = datetime.datetime.fromtimestamp(timestamp)
    return time_

def time_to_str(time_=datetime.datetime.now(), time_format=''):#时间转字符串
    if time_format in ('', None):
        time_format = '%Y-%m-%d %H:%M:%S'
    elif time_format in ('date'):
        time_format = '%Y-%m-%d'
    elif time_format in ('full'):
        time_format = '%Y-%m-%d %H:%M:%S.%f'
    elif time_format in ('without_separator', 'ws'):
        time_format = '%Y%m%d%H%M%S'
    elif time_format in ('date_without_separator', 'dws'):
        time_format = '%Y%m%d'
    elif time_format in ('full_without_separator', 'fws'):
        time_format = '%Y%m%d%H%M%S%f'
    elif time_format in ('year', 'Y'):
        time_format = '%Y'
    elif time_format in ('month', 'm'):
        time_format = '%m'
    elif time_format in ('day', 'd'):
        time_format = '%d'
    elif time_format in ('hour', 'H'):
        time_format = '%H'
    elif time_format in ('minute', 'M'):
        time_format = '%M'
    elif time_format in ('second', 'S'):
        time_format = '%S'
    elif time_format in ('microsecond', 'ms', 'f'):
        time_format = '%f'
    elif time_format in ('week', 'W'):
        time_format = '%W'
    elif time_format in ('week_day', 'wd', 'w'):
        time_format = '%w'
    elif time_format in ('year_day', 'yd', 'j'):
        time_format = '%j'
    elif '%' not in time_format:
        raise ValueError('Invalid format string')
    str_ = time_.strftime(time_format)
    return str_

class Sample:
    def __init__(self, timeStamp, elapsed, success, bytes, sentBytes, responseCode, responseMessage, failureMessage):
        self.timeStamp = timeStamp
        self.elapsed = elapsed
        #self.label = label
        self.success = success
        self.bytes = bytes
        self.sentBytes = sentBytes
        self.completion_time = timeStamp + elapsed
        self.responseCode = responseCode
        self.responseMessage = responseMessage
        self.failureMessage = failureMessage
        
    def __repr__(self):
        return repr((self.timeStamp, self.elapsed))

class AggregateSample:
    def __init__(self, file_name, tl_name):
        self.file_name = file_name
        self.thread_group_name = tl_name[0]
        self.label = tl_name[1]
        self.samples = '0'
        self.average = 0
        self.median = 0
        self._90p_line = 0
        self._95p_line = 0
        self._99p_line = 0
        self.min = 0
        self.max = 0
        self.error_count = 0
        self.error_percent = 0
        self.throughput = 0
        self.received = 0
        self.sent = 0
        self.start_time = 0
        self.end_time = 0
        self.responses = []
        
    def __repr__(self):
        average = int(self.average)
        if self.throughput < 1:
            throughput = str(round(self.throughput*60,1)) + '/min'
        else:
            throughput = str(round(self.throughput,1)) + '/sec'
        if self.received > 1024*1024:
            received = str(round(self.received/1024/1024,2)) + 'MB/sec'
        elif self.received > 1024:
            received = str(round(self.received/1024,2)) + 'KB/sec'
        else:
            received = str(round(self.received,2)) + 'B/sec'
        if self.sent > 1024*1024:
            sent = str(round(self.sent/1024/1024,2)) + 'MB/sec'
        elif self.received > 1024:
            sent = str(round(self.sent/1024,2)) + 'KB/sec'
        else:
            sent = str(round(self.sent,2)) + 'B/sec'
        error = str(round(self.error,2)) + '%'
        return repr((self.file_name, self.thread_group_name, self.label, self.samples, average, self.median, self._90p_line, self._95p_line, self._99p_line, self.min, self.max, error, throughput, received, sent, self.responses))   

def load_csv_into_memory(csv_file, ver='3.1'):
    with open(csv_file, mode='r', encoding='utf-8', newline='') as csvfile: 
    #用with是用来保证运行中出错也可以正确关闭文件的，mode是指定打开方式，newline是指定换行符处理方式
        data = csv.reader(csvfile, delimiter=',', quotechar='"') 
    #delimiter指定分隔符，默认是','，quotechar指定引用符，默认是'"'(双引号)，意思是两个'"'之间的内容会无视换行，分隔等符号，直接输出为一个元素
        i = 0
        sample_group = {}
        column_index = {}
        for line in data:
            #print(line)
            if i == 0:
                j = 0
                for c in line:
                    column_index[c] = j
                    j += 1
                if ver == '3.0':
                    column_index['sentBytes'] = column_index['bytes']
                required_columns = ['timeStamp', 'elapsed', 'label', 'responseCode', 'responseMessage', 'threadName', 'success', 'bytes', 'sentBytes', 'failureMessage']
                for required_column in required_columns:
                    if required_column not in column_index:
                        raise ValueError('missing required column [ ' + required_column +' ]')
            else:
                try:
                    timeStamp = int(line[column_index['timeStamp']])
                    elapsed = int(line[column_index['elapsed']])
                    label = line[column_index['label']]
                    success = line[column_index['success']]
                    bytes = int(line[column_index['bytes']])
                    sentBytes = int(line[column_index['sentBytes']])
                    thread_group_name = line[column_index['threadName']][0:line[column_index['threadName']].rfind(' ')]
                    tl_name = (thread_group_name, label)
                    responseCode = line[column_index['responseCode']]
                    responseMessage = line[column_index['responseMessage']]
                    failureMessage = line[column_index['failureMessage']]
                    if tl_name not in sample_group:
                        sample_group[tl_name] = [Sample(
                                                        timeStamp,
                                                        elapsed,
                                                        #label,
                                                        success,
                                                        bytes,
                                                        sentBytes,
                                                        #threadGroupName,
                                                        responseCode,
                                                        responseMessage,
                                                        failureMessage,
                                                        )]
                    else:
                        sample_group[tl_name].append(Sample(
                                                            timeStamp,
                                                            elapsed,
                                                            #label,
                                                            success,
                                                            bytes,
                                                            sentBytes,
                                                            #threadGroupName,
                                                            responseCode,
                                                            responseMessage,
                                                            failureMessage,
                                                            ))
                except (IndexError,ValueError) as e:
                    continue
            i += 1
        #print(column_index)
        #print(sample_group)
        return sample_group, csv_file

def generate_report_object(sample_group, csv_file):
    report_object = {}
    file_name = csv_file.split(sep='/')[-1].split(sep='\\')[-1]
    if sample_group == {}:
        aggregate_sample = AggregateSample(file_name, ('no data',''))
        report_object[aggregate_sample.label] = aggregate_sample
    else:
        for sample_group_k, sample_group_v in sample_group.items():
            #print(sample_group_k, sample_group_v)
            aggregate_sample = AggregateSample(file_name, sample_group_k)
            aggregate_sample.samples = len(sample_group_v)
            sum_elapsed = 0
            sum_error = 0
            sum_received = 0
            sum_sent = 0
            for sample in sample_group_v:
                sum_elapsed += sample.elapsed
                sum_received += sample.bytes
                sum_sent += sample.sentBytes
                if sample.success.lower() != 'true':
                    sum_error += 1
                if (sample.responseCode, sample.responseMessage, sample.failureMessage) not in aggregate_sample.responses:
                    aggregate_sample.responses.append((sample.responseCode, sample.responseMessage, sample.failureMessage))
            aggregate_sample.average = sum_elapsed/aggregate_sample.samples
            sample_group_v = sorted(sample_group_v, key = lambda x:x.elapsed)
            aggregate_sample.median = sample_group_v[round(aggregate_sample.samples/2)-1].elapsed
            aggregate_sample._90p_line = sample_group_v[round(aggregate_sample.samples*0.9)-1].elapsed
            aggregate_sample._95p_line = sample_group_v[round(aggregate_sample.samples*0.95)-1].elapsed
            aggregate_sample._99p_line = sample_group_v[round(aggregate_sample.samples*0.99)-1].elapsed
            aggregate_sample.min = sample_group_v[0].elapsed
            aggregate_sample.max = sample_group_v[-1].elapsed
            aggregate_sample.error_count = sum_error
            aggregate_sample.error_percent = sum_error/aggregate_sample.samples*100
            sample_group_v = sorted(sample_group_v, key = lambda x:x.timeStamp)
            aggregate_sample.start_time = sample_group_v[0].timeStamp
            sample_group_v = sorted(sample_group_v, key = lambda x:x.completion_time)
            aggregate_sample.end_time = sample_group_v[-1].completion_time
            elapsed_time = aggregate_sample.end_time - aggregate_sample.start_time
            if elapsed_time == 0:
                aggregate_sample.throughput = 'respond time is zero'
                aggregate_sample.received = 'respond time is zero'
                aggregate_sample.sent = 'respond time is zero'
            else:
                aggregate_sample.throughput = aggregate_sample.samples/elapsed_time*1000
                aggregate_sample.received = sum_received/elapsed_time*1000
                aggregate_sample.sent = sum_sent/elapsed_time*1000
            report_object[sample_group_k] = aggregate_sample
    return report_object

def generate_report_csv(csv_file, report_object):
    write_header = 1
    if os.path.exists(csv_file):
        write_header = 0
    with open(csv_file, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', lineterminator='\r\n')
        if write_header:
            writer.writerow(['Name', 'Thread Group', 'Label', '# Samples', 'Average', 'Median', '90% Line', '95% Line', '99% Line', 'Min', 'Max', '# Error', 'Error %', 'Throughput #/sec', 'Received KB/sec', 'Sent KB/sec', 'Start Time', 'End Time', 'Responses'])
        data = []
        for aggregate_sample in report_object.values():
            line = (
                    aggregate_sample.file_name,
                    aggregate_sample.thread_group_name,
                    aggregate_sample.label,
                    aggregate_sample.samples,
                    aggregate_sample.average,
                    aggregate_sample.median,
                    aggregate_sample._90p_line,
                    aggregate_sample._95p_line,
                    aggregate_sample._99p_line,
                    aggregate_sample.min,
                    aggregate_sample.max,
                    aggregate_sample.error_count,
                    aggregate_sample.error_percent,
                    aggregate_sample.throughput,
                    aggregate_sample.received/1024,
                    aggregate_sample.sent/1024,
                    time_to_str(timestamp_to_time(aggregate_sample.start_time/1000)),
                    time_to_str(timestamp_to_time(aggregate_sample.end_time/1000)),
                    aggregate_sample.responses,
                    )
            print(line)
            data.append(line)
        writer.writerows(data)
        csvfile.close()

if __name__ == '__main__':
    #print('START',datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
    if len(argv) < 2:
        sample_group, file_name = load_csv_into_memory('D:\\apache-jmeter-3.1\\results\\test5.csv')
    else:
        sample_group, file_name = load_csv_into_memory(argv[1])
    report_object = generate_report_object(sample_group, file_name)
    #print(report_object)
    if len(argv) < 3:
        now_filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        generate_report_csv('D:\\apache-jmeter-3.1\\results\\aggregate_report_' + now_filename + '.csv', report_object)
    else:
        generate_report_csv(argv[2], report_object)
    #print('END',datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
