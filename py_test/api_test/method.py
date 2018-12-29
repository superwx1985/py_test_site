import datetime
import httplib2
import json
import socket
import logging
from py_test.vic_tools import vic_find_object


# 发送http请求
def send_http_request(vic_step):
    h = httplib2.Http(timeout=vic_step.timeout)
    response_start_time = datetime.datetime.now()
    try:
        response, content = h.request(
            uri=vic_step.api_url, method=vic_step.api_method.upper(), headers=vic_step.api_headers,
            body=vic_step.api_body)
        response_end_time = datetime.datetime.now()
    except socket.timeout as e:
        response_end_time = datetime.datetime.now()
        response = e
        response_body = getattr(e, 'msg', str(e))
    else:
        response_body = ''
        if content:
            try:
                decode = vic_step.api_decode if vic_step.api_decode else 'utf-8'
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
    try:
        save_as_group = json.loads(save_as_group)
    except json.decoder.JSONDecodeError as e:
        raise ValueError('待保存内容无法解析。错误信息：{}'.format(getattr(e, 'msg', str(e))))
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
                            success = False
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
                        success = False
                else:
                    value = content
        msg_ = variables.set_variable(name, value)
        msg_ = '用例' + msg_
        if error_msg:
            msg_ = '{}，所以{}'.format(error_msg, msg_)
        msg = msg + msg_ + '\n'
    return success, msg
