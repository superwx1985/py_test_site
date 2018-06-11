import csv, datetime, os
from sys import argv

class Sample:
    def __init__(self, timeStamp, elapsed, label, success, bytes, sentBytes):
        self.timeStamp = timeStamp
        self.elapsed = elapsed
        self.label = label
        self.success = success
        self.bytes = bytes
        self.sentBytes = sentBytes
        self.finaltime = timeStamp + elapsed
    
    def __repr__(self):
        return repr((self.timeStamp, self.elapsed, self.label))

class AggregateSample:
    def __init__(self, label):
        self.label = label
        self.samples = 0
        self.average = 0
        self.median = 0
        self._90p_line = 0
        self._95p_line = 0
        self._99p_line = 0
        self.min = 0
        self.max = 0
        self.error = 0
        self.throughput = 0
        self.received = 0
        self.sent = 0

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
        return repr((self.label, self.samples, average, self.median, self._90p_line, self._95p_line, self._99p_line, self.min, self.max, error, throughput, received, sent))   

def load_csv_into_memory(csv_file, ver='3.0'):
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
                if 'timeStamp' not in column_index or 'elapsed' not in column_index or 'label' not in column_index or 'success' not in column_index or 'bytes' not in column_index or 'sentBytes' not in column_index:
                    raise ValueError('missing column')
            else:
                if line[column_index['label']] not in sample_group:
                    sample_group[line[column_index['label']]] = [Sample(
                                                                        int(line[column_index['timeStamp']]),
                                                                        int(line[column_index['elapsed']]),
                                                                        line[column_index['label']],
                                                                        line[column_index['success']],
                                                                        int(line[column_index['bytes']]),
                                                                        int(line[column_index['sentBytes']]),
                                                                        )]
                else:
                    sample_group[line[column_index['label']]].append(Sample(
                                                                            int(line[column_index['timeStamp']]),
                                                                            int(line[column_index['elapsed']]),
                                                                            line[column_index['label']],
                                                                            line[column_index['success']],
                                                                            int(line[column_index['bytes']]),
                                                                            int(line[column_index['sentBytes']]),
                                                                            ))
            i += 1
        #print(column_index)
        print(sample_group)
        return sample_group

def generate_report_object(sample_group):
    report_object = {}
    for sample_group_k, sample_group_v in sample_group.items():
        #print(sample_group_k, sample_group_v)
        aggregate_sample = AggregateSample(sample_group_k)
        aggregate_sample.samples = len(sample_group_v)
        sum_elapsed = 0
        sum_error = 0
        sum_received = 0
        sum_sent = 0
        for sample in sample_group_v:
            sum_elapsed += sample.elapsed
            sum_received += sample.bytes
            sum_sent += sample.sentBytes
            if sample.success.lower() == 'false':
                sum_error += 1
        aggregate_sample.average = sum_elapsed/aggregate_sample.samples
        sample_group_v = sorted(sample_group_v, key = lambda x:x.elapsed)
        aggregate_sample.median = sample_group_v[round(aggregate_sample.samples/2)-1].elapsed
        aggregate_sample._90p_line = sample_group_v[round(aggregate_sample.samples*0.9)-1].elapsed
        aggregate_sample._95p_line = sample_group_v[round(aggregate_sample.samples*0.95)-1].elapsed
        aggregate_sample._99p_line = sample_group_v[round(aggregate_sample.samples*0.99)-1].elapsed
        aggregate_sample.min = sample_group_v[0].elapsed
        aggregate_sample.max = sample_group_v[-1].elapsed
        aggregate_sample.error = sum_error/aggregate_sample.samples*100
        sample_group_v = sorted(sample_group_v, key = lambda x:x.timeStamp)
        start_time = sample_group_v[0].timeStamp
        sample_group_v = sorted(sample_group_v, key = lambda x:x.finaltime)
        end_time = sample_group_v[-1].finaltime
        elapsed_time = end_time - start_time
        if elapsed_time == 0:
            aggregate_sample.throughput = 'respond time is zero'
            aggregate_sample.received = 'respond time is zero'
            aggregate_sample.sent = 'respond time is zero'
        else:
            aggregate_sample.throughput = aggregate_sample.samples/elapsed_time*1000
            aggregate_sample.received = sum_received/elapsed_time*1000
            aggregate_sample.sent = sum_sent/elapsed_time*1000
        report_object[aggregate_sample.label] = aggregate_sample
    return report_object

def generate_report_csv(csv_file, report_object):
    write_header = 1
    if os.path.exists(csv_file):
        write_header = 0
    with open(csv_file, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', lineterminator='\r\n')
        if write_header:
            writer.writerow(['Label', '# Samples', 'Average', 'Median', '90% Line', '95% Line', '99% Line', 'Min', 'Max', 'Error %', 'Throughput #/sec', 'Received KB/sec', 'Sent KB/sec'])
        data = []
        for aggregate_sample in report_object.values():
            aggregate_sample.error
            line = (
                     aggregate_sample.label,
                     aggregate_sample.samples,
                     aggregate_sample.average,
                     aggregate_sample.median,
                     aggregate_sample._90p_line,
                     aggregate_sample._95p_line,
                     aggregate_sample._99p_line,
                     aggregate_sample.min,
                     aggregate_sample.max,
                     aggregate_sample.error,
                     aggregate_sample.throughput,
                     aggregate_sample.received/1024,
                     aggregate_sample.sent/1024,
                    )
            #print(line)
            data.append(line)
        writer.writerows(data)
        csvfile.close()

if __name__ == '__main__':
    print('START',datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
    if len(argv) < 2:
        sample_group = load_csv_into_memory('E:\\vic\\性能测试\\results\\test.csv')
    else:
        sample_group = load_csv_into_memory(argv[1])
    report_object = generate_report_object(sample_group)
    print(report_object)
    if len(argv) < 3:
        now_filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        generate_report_csv('E:\\vic\\性能测试\\results\\aggregate_report' + now_filename + '.csv', report_object)
    else:
        generate_report_csv(argv[2], report_object)
    print('END',datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
