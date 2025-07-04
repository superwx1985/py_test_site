import datetime
import requests
import json
import logging
from py_test.vic_tools import vic_find_object
from py_test.vic_test.vic_http_request import vic_requests


def create_session():
    return requests.Session()


# 发送http请求
def send_http_request(vic_step):
    response_start_time = datetime.datetime.now()
    try:
        response = vic_requests(
            method=vic_step.api_method.upper(),
            url=vic_step.api_url,
            headers=vic_step.api_headers,
            files=None,
            data=vic_step.api_body,
            params=None,
            auth=None,
            cookies=None,
            hooks=None,
            json=None,
            _logger=vic_step.logger,
            highlight_error=False,
            timeout=(vic_step.timeout, vic_step.timeout),
            session=vic_step.vic_case.session,
            allow_redirects=vic_step.api_allow_redirects,
            max_redirects=vic_step.api_max_redirects,
        )
    except requests.exceptions.Timeout as e:
        response = e
    response_end_time = datetime.datetime.now()

    return response, response_start_time, response_end_time


# 验证http请求
def verify_http_response(expect_status, expect, response, logger=logging.getLogger('py_test')):
    status_pass = False
    content_pass = False
    pass_group_str = ''
    fail_group_str = ''
    response_text = response.text

    if expect_status and expect_status != str(response.status_code):
        fail_group_str = f'Expected status code is [{expect_status}], but got [{response.status_code}].\n'
    else:
        status_pass = True
        pass_group_str = f'The expected status code and the actual value are the same, both are [{expect_status}].\n'

    if expect:

        content_pass, pass_group, fail_group, condition_count, response_object = vic_find_object.find_with_multiple_condition(
            expect, response_text, logger=logger)

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

        if 0 < len(pass_group):
            pass_group_str += '\n===== Pass Group [%s/%s] =====\n' % (len(pass_group), condition_count)
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

        if 0 < len(fail_group):
            fail_group_str += '\n===== Fail Group [%s/%s] =====\n' % (len(fail_group), condition_count)
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
            response_text = response_text + '\n\nResponse in json view:\n' + json.dumps(response_object, indent=2,
                                                                                   ensure_ascii=False)
    else:
        content_pass = True

    if status_pass and content_pass:
        run_result = ['p', 'PASS\n' + pass_group_str + fail_group_str]
    else:
        run_result = ['f', 'FAIL\n' + pass_group_str + fail_group_str]

    logger.debug(run_result[1])

    return run_result, response_text


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
                header_dict = dict(response.headers)
                header_json = json.dumps(header_dict)
                if expression:
                    value = header_dict.get(expression, None)
                    if not value:
                        find_result = vic_find_object.find_with_condition(expression, header_json, logger=logger)
                        if find_result.is_matched and find_result.re_result:
                            value = find_result.re_result[0]
                        else:
                            error_msg = '响应头中没有找到满足表达式【{}】的内容'.format(expression)
                            if find_result.error_msg:
                                '{}\n在查找过程中出现错误：{}'.format(error_msg, find_result.error_msg)
                            logger.warning(error_msg)
                            value = ''
                            success = False
                else:
                    value = header_json
            else:
                if expression:
                    find_result = vic_find_object.find_with_condition(expression, content, logger=logger)
                    if find_result.is_matched and find_result.re_result:
                        value = find_result.re_result[0]
                    else:
                        error_msg = '响应体中没有找到满足表达式【{}】的内容'.format(expression)
                        if find_result.error_msg:
                            '{}\n在查找过程中出现错误：{}'.format(error_msg, find_result.error_msg)
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
