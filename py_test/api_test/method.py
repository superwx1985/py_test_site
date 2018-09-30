import datetime
import httplib2
import json
import socket
import logging
from py_test.vic_tools import vic_find_object


# 发送http请求
def send_http_request(url, method='GET', headers=None, body=None, timeout=30, logger=logging.getLogger('py_test')):
    method = method.upper()
    if headers:
        try:
            headers = json.loads(headers)
        except ValueError as e:
            logger.error('header格式不正确，请使用正确的json格式', exc_info=True)
            raise ValueError('header格式不正确，请使用正确的json格式。错误信息：{}'.format(getattr(e, 'msg', str(e))))
    else:
        headers = None
    h = httplib2.Http(timeout=timeout)
    response_start_time = datetime.datetime.now()
    str_content = None
    try:
        response, content = h.request(uri=url, method=method, headers=headers, body=body)
        response_end_time = datetime.datetime.now()
    except socket.timeout:
        response_end_time = datetime.datetime.now()
        response = None
        str_content = ''
    else:
        if content is not None:
            try:
                str_content = content.decode('utf-8')  # 处理中文乱码
            except UnicodeDecodeError:
                try:
                    str_content = content.decode('GBK')  # 处理中文乱码
                except UnicodeDecodeError:
                    str_content = str(content)
    return response, str_content, response_start_time, response_end_time


# 验证http请求
def verify_http_response(expect, response, logger=logging.getLogger('py_test')):
    is_pass, pass_group, fail_group, condition_count, response_object = vic_find_object.find_with_multiple_condition(
        expect, response)

    def generate_keyword_str(result):
        param = ''
        expect_count = 'n'
        if result.operator_list:
            param = str(result.operator_list)
            if 'count' in result.operator_list:
                expect_count = result.operator_list[1]
        str_ = '%s\nCount \t[%s]\nExpect\t[%s]\nParam\t%s\n' % (
            result.condition_value, result.match_count, expect_count, param)
        return str_

    pass_group_str = ''
    if 0 < len(pass_group):
        pass_group_str = '\n===== Pass Group [%s/%s] =====\n' % (len(pass_group), condition_count)
        for group_i in pass_group:
            pass_group_str += '----- Group %s [%s/%s] -----\n' % (
                group_i[0], len(group_i[1]), len(group_i[1]) + len(group_i[2]))
            str_p = ''
            str_f = ''
            if 0 < len(group_i[1]):
                str_p = 'Pass keyword:'
                j = 0
                for v in group_i[1]:
                    j += 1
                    str_p += '\n*** Keyword ' + str(j) + ' ***\n' + generate_keyword_str(v[2])
            if 0 < len(group_i[2]):
                str_f = 'Fail keyword:'
                j = 0
                for v in group_i[2]:
                    j += 1
                    str_f += '\n*** Keyword ' + str(j) + ' ***\n' + generate_keyword_str(v[2])
            pass_group_str = pass_group_str + str_p + str_f

    fail_group_str = ''
    if 0 < len(fail_group):
        fail_group_str = '\n===== Fail Group [%s/%s] =====\n' % (len(fail_group), condition_count)
        for group_i in fail_group:
            fail_group_str += '----- Group %s [%s/%s] -----\n' % (
                group_i[0], len(group_i[1]), len(group_i[1]) + len(group_i[2]))
            str_p = ''
            str_f = ''
            if 0 < len(group_i[1]):
                str_p = 'Pass keyword:'
                j = 0
                for v in group_i[1]:
                    j += 1
                    str_p += '\n*** Keyword ' + str(j) + ' ***\n' + generate_keyword_str(v[2])
            if 0 < len(group_i[2]):
                str_f = 'Fail keyword:'
                j = 0
                for v in group_i[2]:
                    j += 1
                    str_f += '\n*** Keyword ' + str(j) + ' ***\n' + generate_keyword_str(v[2])
            fail_group_str = fail_group_str + str_p + str_f
    if isinstance(response_object, (tuple, list, dict)):
        response = str(response) + '\n\nResponse in json view:\n' + json.dumps(response_object, indent=1,
                                                                               ensure_ascii=False)
        response = str(response) + '\n\nResponse in object view:\n' + str(response_object)
    if is_pass:
        run_result = ('p', 'PASS\n' + pass_group_str + fail_group_str + '\nResponse:\n' + str(response))
    else:
        run_result = ('f', 'FAIL\n' + pass_group_str + fail_group_str + '\nResponse:\n' + str(response))
    logger.debug(run_result[1])

    return run_result


# 获取响应内容，保存为变量
def save_http_response(response, content, save_as_group, variables, logger=logging.getLogger('py_test')):
    success = True
    msg = ''
    for save_as in save_as_group:
        error_msg = None
        try:
            name = save_as['name']
            part = save_as['part']
            expression = save_as['expression']
        except KeyError:
            continue
        else:
            if part == '1':
                if expression:
                    value = response.get(expression, None)
                    if not value:
                        error_msg = '响应头中没有找到键为【{}】的值'.format(expression)
                        logger.warning(error_msg)
                        value = ''
                else:
                    value = json.dumps(response)
            else:
                if expression:
                    find_result = vic_find_object.find_with_condition(expression, content, logger)
                    if find_result.is_matched and find_result.re_result:
                        value = find_result.re_result[0]
                    else:
                        error_msg = '响应体中没有找到满足正则表达式【{}】的内容'.format(expression)
                        logger.warning(error_msg)
                        value = ''
                else:
                    value = content
        msg_ = variables.set_variable(name, value, 1000)
        if error_msg:
            msg_ = '{}\n{}'.format(error_msg, msg_)
        msg = msg + '用例' + msg_ + '\n'
    return success, msg
