import datetime
import httplib2
import json
import socket
import logging
from py_test.vic_tools import vic_find_object


# 发送http请求
def send_http_request(
        url, method='GET', headers=None, body=None, decode='', timeout=30, logger=logging.getLogger('py_test')):
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
    try:
        response, content = h.request(uri=url, method=method, headers=headers, body=body)
        response_end_time = datetime.datetime.now()
    except socket.timeout:
        response_end_time = datetime.datetime.now()
        response = None
        response_body = ''
    else:
        response_body = None
        if content is not None:
            try:
                decode = decode if decode else 'utf-8'
                response_body = content.decode(decode)  # 处理中文乱码
            except UnicodeDecodeError:
                response_body = str(content)
    return response, response_body, response_start_time, response_end_time


# 验证http请求
def verify_http_response(expect, response, logger=logging.getLogger('py_test')):
    is_pass, pass_group, fail_group, condition_count, response_object = vic_find_object.find_with_multiple_condition(
        expect, response, logger=logger)

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

    if is_pass:
        run_result = ['p', 'PASS\n' + pass_group_str + fail_group_str]
    else:
        run_result = ['f', 'FAIL\n' + pass_group_str + fail_group_str]
    logger.debug(run_result[1])

    return run_result, response


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
            if part == 'header':
                response_json = json.dumps(response)
                if expression:
                    value = response.get(expression, None)
                    if not value:
                        find_result = vic_find_object.find_with_condition(expression, dict(response), logger=logger)
                        if find_result.is_matched and find_result.re_result:
                            value = find_result.re_result[0]
                        else:
                            error_msg = '响应头中没有找到满足表达式【{}】的内容'.format(expression)
                            logger.warning(error_msg)
                            value = ''
                else:
                    value = response_json
            else:
                if expression:
                    find_result = vic_find_object.find_with_condition(expression, content, logger=logger)
                    if find_result.is_matched and find_result.re_result:
                        value = find_result.re_result[0]
                    else:
                        error_msg = '响应体中没有找到满足表达式【{}】的内容'.format(expression)
                        logger.warning(error_msg)
                        value = ''
                else:
                    value = content
        msg_ = variables.set_variable(name, value, 1000)
        msg_ = '用例' + msg_
        if error_msg:
            msg_ = '{}（{}）'.format(msg_, error_msg)
        msg = msg + msg_ + '\n'
    return success, msg
