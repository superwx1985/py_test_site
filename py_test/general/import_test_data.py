import os
import csv
import xlrd
from py_test.vic_tools import vic_excel_col_change
from py_test.general.vic_log import get_thread_logger


def get_csv_data(filename, print_=False):
    csv_data = []
    # 用with是用来保证运行中出错也可以正确关闭文件的，mode是指定打开方式，newline是指定换行符处理方式
    with open(filename, mode='r', newline='') as file:
        # delimiter指定分隔符，默认是','，quotechar指定引用符，默认是'"'，这里指定了'|'，意思是两个'|'直接的内容会无视换行，分隔等符号，直接输出为一个元素
        data = csv.reader(file, delimiter=',', quotechar='|')
    for line in data:
        if print_:
            print(line)
        csv_data.append(line)
    return csv_data


def get_txt_data(filename, print_=False):
    with open(filename, mode='r') as file:
        data = file.readlines()
    if print_:
        for line in data:
            print(line)
    return data


def get_excel_data(filename, sheet_name):
    logger = get_thread_logger()
    data = {}
    with xlrd.open_workbook(filename) as workbook:
        sheet = workbook.sheet_by_name(sheet_name)
        data['file'] = filename
        data['sheet'] = sheet_name
        data['rows'] = sheet.nrows
        data['columns'] = sheet.ncols
        logger.debug(
            '打开excel文件【%s】，读取工作表【%s】，此工作表共有%s行，%s列' % (data['file'], data['sheet'], data['rows'], data['columns']))
        msg = ''
        for r in range(0, sheet.nrows):
            rname = str(r + 1)
            for c in range(0, sheet.ncols):
                cname = vic_excel_col_change.dec_to_excel_col(c + 1)
                data[cname + rname] = sheet.cell(r, c).value
                msg = '%s\t\t[%s%s]%s' % (msg, cname, str(r + 1), str(sheet.cell(r, c).value))
                # print('[' + cname + str(r + 1) + ']' + str(sheet.cell(r, c).value) + '\t\t', end='')
                if c + 1 == sheet.ncols:
                    msg = msg + '\n'
        logger.debug('工作表数据：\n%s' % msg)
    return data


def get_matched_file_list(_dir, ignore='', prefix='', suffix='', keyword=''):
    logger = get_thread_logger()
    import copy
    file_list = sorted(os.listdir(_dir))
    logger.debug('*** 文件夹内的全部文件 ***')
    logger.debug(file_list)

    if isinstance(ignore, str):
        ignore_list_temp = ignore.replace('\n', '').lower().split(sep=',')
        ignore_list = list()
        for p in ignore_list_temp:
            if p.strip() != '':
                ignore_list.append(p)
    else:
        raise ValueError('ignore should be string')
    if isinstance(prefix, str):
        prefix_list_temp = prefix.replace('\n', '').lower().split(sep=',')
        prefix_list = list()
        for p in prefix_list_temp:
            if p.strip() != '':
                prefix_list.append(p)
    else:
        raise ValueError('prefix should be string')
    if isinstance(suffix, str):
        # 转为小写并且去除全部空格
        suffix = suffix.replace('\n', '').lower().replace(' ', '').split(sep=',')
    else:
        raise ValueError('suffix should be string')
    if isinstance(keyword, str):
        keyword_list_temp = keyword.replace('\n', '').lower().split(sep=',')
        keyword_list = list()
        for p in keyword_list_temp:
            if p.strip() != '':
                keyword_list.append(p)
    else:
        raise ValueError('keyword should be string')

    temp_list = copy.deepcopy(file_list)  # 拷贝list，不能直接list1=list2，那样只会把list1指向list2
    # 排除特定名称的文件
    for file in file_list:
        for ignore_str in ignore_list:
            if ignore_str in os.path.splitext(file)[0]:
                temp_list.remove(file)
    file_list = copy.deepcopy(temp_list)
    logger.debug('*** 排除特定名称的文件 ***')
    logger.debug(file_list)
    temp_list = copy.deepcopy(file_list)
    # 排除后缀不符合的文件
    for file in file_list:
        if os.path.splitext(file)[1].replace('.', '') not in suffix:
            temp_list.remove(file)
    file_list = copy.deepcopy(temp_list)
    logger.debug('*** 排除后缀不符合的文件 ***')
    logger.debug(file_list)
    # 排除前缀不符合的文件
    file_list2 = list()
    if len(prefix_list) == 0:
        file_list2 = file_list
    else:
        for x in prefix_list:
            x = x.strip()
            file_list = copy.deepcopy(temp_list)  # 如出现相同的prefix，重新赋值可以防止从temp_list移除不存在file导致的报错
            for file in file_list:
                if file[0:len(x)].lower() == x and x != '':
                    file_list2.append(file)
                    temp_list.remove(file)
        temp_list = copy.deepcopy(file_list2)
    logger.debug('*** 排除前缀不符合的文件 ***')
    logger.debug(file_list2)
    # 排除关键字不符合的文件
    matched_file_list = list()
    if len(keyword_list) == 0:
        matched_file_list = file_list2
    else:
        for x in keyword_list:
            x = x.strip()
            file_list2 = copy.deepcopy(temp_list)  # 如出现相同的keyword，重新赋值可以防止从temp_list移除不存在file导致的报错
            x = x.split(sep='+')
            for file in file_list2:
                if keyword == ['']:
                    matched_file_list.append(file)
                else:
                    match = 0
                    valid_len = 0
                    for y in x:
                        if y != '':
                            valid_len += 1
                            if y in file[0:file.rfind('.')].lower():
                                match += 1
                    if valid_len == match and match > 0:
                        matched_file_list.append(file)
                        temp_list.remove(file)
    logger.debug('*** 排除关键字不符合的文件 ***')
    logger.debug(matched_file_list)
    return matched_file_list


if __name__ == '__main__':
    from py_test.general.vic_log import init_logger

    init_logger(log_level=10, console_log_level=20)
    # base_dir = os.path.dirname(__file__)
    base_dir = 'D:/vic/debug'
    # data=get_csv_data('D:/vic/workspace/PyTest01/KWS/test_data/address.csv',True)
    # print(data[1][1])
    # get_txt_data('D:/vic/workspace/PyTest01/vic_test/text1.txt', True)
    excel_data = get_excel_data(base_dir + '/TC/niumo-PROD-获取问卷-男性-成年-v2.0.xlsx', 'TC')
    col_map = {}
    for col in range(1, excel_data['columns'] + 1):
        col = vic_excel_col_change.dec_to_excel_col(col)
        col_map[excel_data[col + '1']] = col
    col_check_list = ('name', 'action', 'by', 'locator', 'index', 'data', 'timeout', 'skip', 'save as',)
    for col in col_check_list:
        if col not in col_map:
            raise ValueError('Missing column "' + col + '" in the test case file!')
    step_name = excel_data[col_map['data'] + str(2)]
    print(step_name)
