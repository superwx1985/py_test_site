import time
import json
import logging
from selenium.common import exceptions
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.action_chains import ActionChains
from py_test.vic_tools import vic_find_object, vic_eval
from py_test.vic_tools.vic_str_handle import convert_string_to_float
from py_test.general import vic_variables
from py_test.web_ui_test import driver
from selenium.webdriver.common.by import By


def check_web_driver(step):
    if not step.drs.get("web_dr", None):
        # 初始化driver
        step.logger.info('【{}】\t启动浏览器...'.format(step.execute_str))
        dr = driver.get_driver(step.config, step.execute_str, 3, step.timeout, logger=step.logger)
        step.drs["web_dr"] = dr
        # raise exceptions.WebDriverException('浏览器未初始化，请检查是否配置有误或浏览器被意外关闭')


# 设置UI测试驱动超时
def set_driver_timeout(dr, timeout):
    # 设置selenium超时时间
    dr.implicitly_wait(timeout)
    dr.set_page_load_timeout(timeout)
    dr.set_script_timeout(timeout)
    # 设置Remote Connection超时时间
    dr.command_executor.set_timeout(int(timeout + 5))


# 获取公共元素
def get_public_elements(vic_step):
    name = vic_step.ui_locator
    public_elements = vic_step.public_elements
    try:
        element_info = public_elements.get_element_info(name)
    except KeyError:
        raise ValueError('找不到公共元素【{}】'.format(name))
    element_by = element_info[0]
    element_locator = element_info[1]
    return element_by, element_locator


# 元素高亮
def highlight(dr, elements, color='green'):
    style = 'outline: 2px dotted %s; border: 1px solid %s;' % (color, color)
    highlight_elements_map = {}
    for element in elements:
        original_style = dr.execute_script(
            '''let element = arguments[0];
            let original_style = element.getAttribute("style")?element.getAttribute("style"):"";
            element.setAttribute("style", original_style + "; ''' + style + '''");
            return original_style;''', element)
        highlight_elements_map[element] = original_style
    return highlight_elements_map


# 元素取消高亮
def cancel_highlight(dr, elements_map):
    for element, original_style in elements_map.items():
        try:
            dr.execute_script(
                '''let element = arguments[0];
                let original_style = arguments[1];
                element.setAttribute("style", original_style + ";");''',
                element, original_style)
        except exceptions.StaleElementReferenceException:
            pass  # 如果元素此时已被刷新，则忽略本操作


# 元素高亮N秒
def highlight_for_a_moment(dr, elements, color='green', duration=0.5, sleep=0):
    # background-color: rgba(255, 0, 0, 0.7)
    style = 'outline: 2px dotted %s; border: 1px solid %s;' % (color, color)
    for element in elements:
        dr.execute_script(
            '''let element = arguments[0];
            let original_style = element.getAttribute("style")?element.getAttribute("style"):"";
            element.setAttribute("style", original_style + "; ''' + style + '''");
            setTimeout(function(){element.setAttribute("style", original_style);}, ''' + str(
                round(duration * 1000)) + ');', element)
    if sleep:
        time.sleep(sleep)


# 等待文字出现
def wait_for_text_present(vic_step, print_=True):
    pause_time = 0
    elements = list()
    fail_elements = list()
    index_ = vic_step.ui_index
    text = vic_step.ui_data
    _success = False
    _full_msg = ''
    msg = '没找到期望文字【{}】'.format(text)
    msg_format = '经过{:.1f}秒 - {}'
    vic_step.drs['web_dr'].implicitly_wait(0)
    last_print_time = start_time = time.time()
    while (time.time() - start_time - pause_time) <= vic_step.timeout and not vic_step.force_stop:
        elements.clear()
        fail_elements.clear()
        if not vic_step.ui_by and not vic_step.ui_locator:
            _body = vic_step.drs['web_dr'].find_element(By.TAG_NAME, 'body')
            find_result = vic_find_object.find_with_condition(text, _body.text, logger=vic_step.logger)
            if find_result.is_matched:
                elements_temp = vic_step.drs['web_dr'].find_elements(By.XPATH, '//body//*[contains(text(),"' + text + '")]')
                for element in elements_temp:
                    if element.is_displayed():
                        elements.append(element)
                if not elements:  # 如果文本不在元素的第一个子节点，用text()可能会找不到
                    elements.append(_body)
                msg = '在页面找到期望文字【{}】'.format(text)
                _success = True
            elif find_result.error_msg:
                msg = '没找到期望文字【{}】\n在查找过程中出现错误：{}'.format(text, find_result.error_msg)
        else:
            _ui_data = vic_step.ui_data
            vic_step.ui_data = None  # 把ui_data置空，防止查找元素时被当做数量限制表达式
            _start_time = time.time()
            _pause_time = 0
            run_result_temp = ['f', 'N/A']
            elements_temp = None
            try:
                run_result_temp, elements_temp, elements_all, _, _pause_time = wait_for_element_visible(
                    vic_step, timeout=1, print_=False)
            except:
                _elapsed_time = time.time() - _start_time
                _pause_time = 0 if _elapsed_time < 1.5 else _elapsed_time - 1.5
            finally:
                pause_time += _pause_time
                vic_step.ui_data = _ui_data
            if run_result_temp[0] == 'f':
                msg = '未找到期望元素【By:{}|Locator:{}】或元素不可见'.format(vic_step.ui_by, vic_step.ui_locator)
            else:
                _error_msg = None
                if index_ is None:
                    for element_temp in elements_temp:
                        # element_text = vic_step.drs['web_dr'].execute_script(
                        #     'return arguments[0].textContent||arguments[0].innerText||arguments[0].value',
                        #     element_temp)
                        element_text = element_temp.get_attribute('value') or element_temp.text
                        find_result = vic_find_object.find_with_condition(text, element_text, logger=vic_step.logger)
                        if find_result.is_matched:
                            elements.append(element_temp)
                        else:
                            fail_elements.append(element_temp)
                            if find_result.error_msg:
                                if _error_msg:
                                    _error_msg = '{};{}'.format(_error_msg, find_result.error_msg)
                                else:
                                    _error_msg = find_result.error_msg
                elif index_ > (len(elements_temp) - 1):
                    raise ValueError('找到{}个元素，但指定的索引【{}】超出可用范围（0到{}）'.format(
                        len(elements), index_, len(elements) - 1))
                else:
                    element_text = vic_step.drs['web_dr'].execute_script(
                        'return arguments[0].textContent||arguments[0].innerText||arguments[0].value',
                        elements_temp[index_])
                    find_result = vic_find_object.find_with_condition(text, element_text, logger=vic_step.logger)
                    if find_result.is_matched:
                        elements.append(elements_temp[index_])
                    else:
                        fail_elements.append(elements_temp[index_])
                        if find_result.error_msg:
                            _error_msg = find_result.error_msg
                msg = '找到期望元素【By:{}|Locator:{}】{}个，其中有{}个元素包含期望文字【{}】'.format(
                    vic_step.ui_by, vic_step.ui_locator, len(elements_temp), len(elements), text)
                if _error_msg:
                    msg = '{}\n在查找过程中出现错误：{}'.format(msg, _error_msg)
            if elements and not fail_elements:
                _success = True

        if time.time() - last_print_time >= 1:
            pause_time += vic_step.pause_()
            elapsed_time = time.time() - start_time - pause_time
            _full_msg = msg_format.format(elapsed_time, msg)
            if print_:
                vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, _full_msg))
            last_print_time = time.time()

        if _success:
            break

    elapsed_time = time.time() - start_time - pause_time
    full_msg = msg_format.format(elapsed_time, msg)
    if print_ and full_msg != _full_msg:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, full_msg))
    if _success:
        run_result = ['p', full_msg]
    else:
        run_result = ['f', full_msg]
    vic_step.drs['web_dr'].implicitly_wait(vic_step.timeout)
    return run_result, elements, fail_elements, elapsed_time, pause_time


# 等待元素出现
def wait_for_element_present(vic_step, timeout=None, print_=True):
    pause_time = 0
    _full_msg = ''
    elements = list()
    if not timeout:
        timeout = vic_step.timeout
    msg = '未找到期望元素【By:{}|Locator:{}】'.format(vic_step.ui_by, vic_step.ui_locator)
    msg_format = '经过{:.1f}秒 - {}'
    vic_step.drs['web_dr'].implicitly_wait(0)
    last_print_time = start_time = time.time()
    while (time.time() - start_time - pause_time) <= timeout and not vic_step.force_stop:
        if vic_step.variable_elements:
            elements = vic_step.variable_elements
        else:
            if isinstance(vic_step.ui_base_element, WebElement):
                elements = vic_step.ui_base_element.find_elements(vic_step.ui_by, vic_step.ui_locator)
            else:
                elements = vic_step.drs['web_dr'].find_elements(vic_step.ui_by, vic_step.ui_locator)

        msg = '找到期望元素【By:{}|Locator:{}】{}个'.format(vic_step.ui_by, vic_step.ui_locator, len(elements))

        if time.time() - last_print_time >= 1:
            pause_time += vic_step.pause_()
            elapsed_time = time.time() - start_time - pause_time
            _full_msg = msg_format.format(elapsed_time, msg)
            if print_:
                vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, _full_msg))
            last_print_time = time.time()

        if elements:
            break

    elapsed_time = time.time() - start_time - pause_time
    full_msg = msg_format.format(elapsed_time, msg)
    if print_ and full_msg != _full_msg:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, full_msg))
    if elements:
        run_result = ['p', full_msg]
    else:
        run_result = ['f', full_msg]
    vic_step.drs['web_dr'].implicitly_wait(timeout)
    return run_result, elements, elapsed_time, pause_time


# 获取元素
def get_element(vic_step, timeout=None, print_=True, necessary=True):
    element = None
    el_msg = ''
    err_msg = ''
    if not timeout:
        timeout = vic_step.timeout
    run_result_temp, elements, elapsed_time, pause_time = wait_for_element_present(
        vic_step, timeout=timeout, print_=print_)
    if run_result_temp[0] == 'f':
        err_msg = '未找到元素，错误信息：{}'.format(run_result_temp[1])
    elif len(elements) == 1 and vic_step.ui_index in (None, 0):
        el_msg = '【By:{}|Locator:{}】'.format(vic_step.ui_by, vic_step.ui_locator)
        element = elements[0]
    elif vic_step.ui_index is None:
        err_msg = '找到{}个元素，请指定索引获取唯一元素'.format(len(elements))
    elif vic_step.ui_index > (len(elements) - 1):
        err_msg = '找到{}个元素，但指定的索引【{}】超出可用范围（0到{}）'.format(
            len(elements), vic_step.ui_index, len(elements)-1)
    else:
        el_msg = '【By:{}|Locator:{}|Index:{}】'.format(vic_step.ui_by, vic_step.ui_locator, vic_step.ui_index)
        element = elements[vic_step.ui_index]
    if not element and necessary:
        raise exceptions.NoSuchElementException(err_msg)
    return element, el_msg, err_msg, elapsed_time, pause_time


# 等待元素可见
def wait_for_element_visible(vic_step, timeout=None, print_=True):
    pause_time = 0
    elements = list()
    visible_elements = list()
    if not timeout:
        timeout = vic_step.timeout
    _success = False
    _full_msg = ''
    msg = '未找到期望元素【By:{}|Locator:{}】'.format(vic_step.ui_by, vic_step.ui_locator)
    msg_format = '经过{:.1f}秒 - {}'
    vic_step.drs['web_dr'].implicitly_wait(0)
    last_print_time = start_time = time.time()
    while (time.time() - start_time - pause_time) <= timeout and not vic_step.force_stop:
        visible_elements.clear()
        if vic_step.variable_elements:
            elements = vic_step.variable_elements
        else:
            if isinstance(vic_step.ui_base_element, WebElement):
                elements = vic_step.ui_base_element.find_elements(vic_step.ui_by, vic_step.ui_locator)
            else:
                elements = vic_step.drs['web_dr'].find_elements(vic_step.ui_by, vic_step.ui_locator)
        if elements:
            for element in elements:
                if element.is_displayed():
                    visible_elements.append(element)

        msg = '找到期望元素【By:{}|Locator:{}】{}个，其中可见元素{}个'.format(
            vic_step.ui_by, vic_step.ui_locator, len(elements), len(visible_elements))
        if vic_step.ui_data:
            eo = vic_eval.EvalObject(vic_step.ui_data, {'x': len(visible_elements)}, vic_step.logger)
            eval_success, eval_result, final_expression = eo.get_eval_result()
            compare_result = eval_result
            if compare_result is True:
                msg = '{}，符合给定的数量限制\n数量表达式：{}'.format(msg, final_expression)
                _success = True
            else:
                msg = '{}，不符合给定的数量限制\n数量表达式：{}'.format(msg, final_expression)
        elif visible_elements:
            _success = True

        if time.time() - last_print_time >= 1:
            pause_time += vic_step.pause_()
            elapsed_time = time.time() - start_time - pause_time
            _full_msg = msg_format.format(elapsed_time, msg)
            if print_:
                vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, _full_msg))
            last_print_time = time.time()

        if _success:
            break

    elapsed_time = time.time() - start_time - pause_time
    full_msg = msg_format.format(elapsed_time, msg)
    if print_ and full_msg != _full_msg:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, full_msg))
    if _success:
        run_result = ['p', full_msg]
    else:
        run_result = ['f', full_msg]
    vic_step.drs['web_dr'].implicitly_wait(timeout)
    return run_result, visible_elements, elements, elapsed_time, pause_time


# 获取可见元素
def get_visible_element(vic_step, timeout=None, print_=True, necessary=True):
    element = None
    el_msg = ''
    err_msg = ''
    if not timeout:
        timeout = vic_step.timeout
    _ui_data = vic_step.ui_data
    vic_step.ui_data = None  # 把ui_data置空，防止查找元素时被当做数量限制表达式
    try:
        run_result_temp, elements, _, elapsed_time, pause_time = wait_for_element_visible(vic_step, timeout=timeout, print_=print_)
    finally:
        vic_step.ui_data = _ui_data
    if run_result_temp[0] == 'f':
        err_msg = '未找到元素，错误信息：{}'.format(run_result_temp[1])
    elif len(elements) == 1 and vic_step.ui_index in (None, 0):
        el_msg = '【By:{}|Locator:{}】'.format(vic_step.ui_by, vic_step.ui_locator)
        element = elements[0]
    elif vic_step.ui_index is None:
        err_msg = '找到{}个元素，请指定索引获取唯一元素'.format(len(elements))
    elif vic_step.ui_index > (len(elements) - 1):
        err_msg = '找到{}个元素，但指定的索引【{}】超出可用范围（0到{}）'.format(
            len(elements), vic_step.ui_index, len(elements) - 1)
    else:
        el_msg = '【By:{}|Locator:{}|Index:{}】'.format(vic_step.ui_by, vic_step.ui_locator, vic_step.ui_index)
        element = elements[vic_step.ui_index]
    if not element and necessary:
        raise exceptions.NoSuchElementException(err_msg)
    return element, el_msg, err_msg, elapsed_time, pause_time


# 等待元素消失
def wait_for_element_disappear(vic_step, print_=True):
    pause_time = 0
    visible_elements = list()
    _success = False
    _full_msg = ''
    msg = '未找到期望元素【By:{}|Locator:{}】'.format(vic_step.ui_by, vic_step.ui_locator)
    msg_format = '经过{:.1f}秒 - {}'
    vic_step.drs['web_dr'].implicitly_wait(0)
    last_print_time = start_time = time.time()
    while (time.time() - start_time - pause_time) <= vic_step.timeout and not vic_step.force_stop:
        visible_elements = list()
        if vic_step.variable_elements:
            elements = vic_step.variable_elements
        else:
            if isinstance(vic_step.ui_base_element, WebElement):
                elements = vic_step.ui_base_element.find_elements(vic_step.ui_by, vic_step.ui_locator)
            else:
                elements = vic_step.drs['web_dr'].find_elements(vic_step.ui_by, vic_step.ui_locator)

        for element in elements:
            if element.is_displayed():
                visible_elements.append(element)
        if elements and not visible_elements:
            _success = True

        msg = '找到期望元素【By:{}|Locator:{}】{}个，其中可见元素{}个'.format(
            vic_step.ui_by, vic_step.ui_locator, len(elements), len(visible_elements))

        if time.time() - last_print_time >= 1:
            pause_time += vic_step.pause_()
            elapsed_time = time.time() - start_time - pause_time
            _full_msg = msg_format.format(elapsed_time, msg)
            if print_:
                vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, _full_msg))
            last_print_time = time.time()

        if _success:
            break

    elapsed_time = time.time() - start_time - pause_time
    full_msg = msg_format.format(elapsed_time, msg)
    if print_ and full_msg != _full_msg:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, full_msg))
    if _success:
        run_result = ['p', full_msg]
    else:
        run_result = ['f', full_msg]
    vic_step.drs['web_dr'].implicitly_wait(vic_step.timeout)
    return run_result, visible_elements, elapsed_time, pause_time


# 跳转到url
def go_to_url(vic_step):
    url = vic_step.ui_data
    vic_step.drs['web_dr'].get(url)
    run_result = ['p', '成功打开URL【{}】'.format(url)]
    return run_result


# 等待页面跳转
def wait_for_page_redirect(vic_step, print_=True):
    pause_time = 0
    _success = False
    _full_msg = ''
    msg = '新URL不符合期望【{}】'.format(vic_step.ui_data)
    msg_format = '经过{:.1f}秒 - {}'
    last_print_time = start_time = time.time()
    _error_msg = None
    while (time.time() - start_time - pause_time) <= vic_step.timeout and not vic_step.force_stop:
        current_url = vic_step.drs['web_dr'].current_url
        find_result = vic_find_object.find_with_condition(vic_step.ui_data, current_url, logger=vic_step.logger)
        if find_result.is_matched:
            msg = '新URL符合期望【{}】'.format(vic_step.ui_data)
            _success = True
        elif find_result.error_msg:
            _error_msg = find_result.error_msg
            msg = '新URL不符合期望【{}】\n在查找过程中出现错误：{}'.format(vic_step.ui_data, _error_msg)

        if time.time() - last_print_time >= 1:
            pause_time += vic_step.pause_()
            elapsed_time = time.time() - start_time - pause_time
            _full_msg = msg_format.format(elapsed_time, msg)
            if print_:
                vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, _full_msg))
            last_print_time = time.time()

        if _success or _error_msg:
            break

    elapsed_time = time.time() - start_time - pause_time
    full_msg = msg_format.format(elapsed_time, msg)
    if print_ and full_msg != _full_msg:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, full_msg))
    if _success:
        run_result = ['p', full_msg]
    else:
        run_result = ['f', full_msg]
    return run_result, elapsed_time, pause_time


# 获取URL
def get_url(vic_step, print_=True):
    url = vic_step.drs['web_dr'].current_url
    condition_value = vic_step.ui_data

    if condition_value:
        find_result = vic_find_object.find_with_condition(condition_value, url, logger=vic_step.logger)
        if find_result.is_matched:
            if find_result.re_result:
                url = vic_find_object.get_first_text_in_re_result(find_result.re_result)
            run_result = ['p', '找到符合条件【{}】的URL内容【{}】'.format(condition_value, url)]
        else:
            msg = '找不到符合条件【{}】的URL内容'.format(condition_value)
            if find_result.error_msg:
                msg = '{}\n在查找过程中出现错误：{}'.format(msg, find_result.error_msg)
            run_result = ['f', msg]
    else:
        run_result = ['p', '获取到URL【{}】'.format(url)]
    if print_:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, run_result[1]))
    return run_result, url


# 尝试点击
def try_to_click(vic_step, print_=True):
    def func(**kwargs):
        element = kwargs['element']
        el_msg = kwargs['el_msg']
        element.click()
        msg = '点击元素{}'.format(el_msg)
        return msg

    return try_to_do(vic_step, func, print_)


# 尝试输入
def try_to_enter(vic_step, print_=True):
    def func(**kwargs):
        element = kwargs['element']
        el_msg = kwargs['el_msg']
        element.send_keys(vic_step.ui_data)
        msg = '在元素{}中输入【{}】'.format(el_msg, vic_step.ui_data)
        return msg

    return try_to_do(vic_step, func, print_)


# 尝试清空
def try_to_clear(vic_step, print_=True):
    def func(**kwargs):
        element = kwargs['element']
        el_msg = kwargs['el_msg']
        _value = element.get_attribute('value')
        element.clear()
        msg = '清空元素{}的内容，原内容为{}'.format(el_msg, _value)
        return msg

    return try_to_do(vic_step, func, print_)


# 尝试操作元素
def try_to_do(vic_step, func, print_=True):
    err = None
    _success = False
    _full_msg = ''
    msg = '超时'
    msg_format = '经过{:.1f}秒 - {}'
    pause_time = 0
    element, el_msg, err_msg, _elapsed_time, _pause_time = get_element(vic_step, print_=print_, necessary=False)
    pause_time += _pause_time

    if element:
        vic_step.drs['web_dr'].implicitly_wait(0)
        timeout = vic_step.timeout - _elapsed_time if vic_step.timeout - _elapsed_time > 1 else 1
        highlight_for_a_moment(vic_step.drs['web_dr'], [element], 'outline: 2px dotted yellow; border: 1px solid yellow;')
        last_print_time = start_time = time.time()
        while (time.time() - start_time - pause_time) <= timeout and not vic_step.force_stop:
            err = None
            try:
                msg = func(element=element, el_msg=el_msg)
                _success = True
            except exceptions.ElementNotVisibleException as e:
                err = e
                msg = '无法操作元素{}，因为不可见'.format(el_msg)
            except exceptions.InvalidElementStateException as e:
                err = e
                msg = '无法操作元素{}，因为无法交互，例如元素被设置为disabled'.format(el_msg)
            except exceptions.WebDriverException as e:
                _err_msg = 'element is not attached to the page document'
                if isinstance(e, exceptions.StaleElementReferenceException) or _err_msg in e.msg:
                    raise  # 如果是元素过期，直接抛出异常让step处理
                else:
                    err = e
                    msg = '无法操作元素{}，因为{}'.format(el_msg, getattr(e, 'msg', str(e)))

                # _err_msg = 'element is not attached to the page document'
                # if isinstance(e, exceptions.StaleElementReferenceException) or _err_msg in e.msg:
                #     msg = '无法操作元素{}，可能是由于页面异步刷新导致，将尝试重新获取元素'.format(el_msg)
                #     _timeout = timeout - (time.time() - start_time - pause_time)
                #     element, el_msg, err_msg, _elapsed_time, _pause_time = get_element(
                #         vic_step, timeout=_timeout, print_=print_, necessary=False)
                #     pause_time += _pause_time
                # else:
                #     err = e
                #     msg = '无法操作元素{}，因为{}'.format(el_msg, getattr(e, 'msg', str(e)))

            if time.time() - last_print_time >= 1:
                pause_time += vic_step.pause_()
                elapsed_time = time.time() - start_time - pause_time + _elapsed_time
                _full_msg = msg_format.format(elapsed_time, msg)
                if print_:
                    vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, _full_msg))
                last_print_time = time.time()

            if _success:
                break
        vic_step.drs['web_dr'].implicitly_wait(vic_step.timeout)
    else:
        err = exceptions.NoSuchElementException(err_msg)
        msg = err_msg
        start_time = time.time()

    elapsed_time = time.time() - start_time - pause_time + _elapsed_time
    full_msg = msg_format.format(elapsed_time, msg)
    if print_ and full_msg != _full_msg:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, full_msg))
    if _success:
        run_result = ['p', full_msg]
    else:
        if err:
            err.msg = full_msg
            raise err
        else:
            raise exceptions.WebDriverException(full_msg)
    return run_result, element, elapsed_time, pause_time


# 尝试选择
def try_to_select(vic_step, print_=True):
    element, el_msg, _, elapsed_time, pause_time = get_visible_element(vic_step, print_=print_)
    highlight_for_a_moment(vic_step.drs['web_dr'], (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    select = Select(element)
    # 如果data为空则全不选
    if not vic_step.ui_data:
        select.deselect_all()
    # 如果data为字符串all
    elif vic_step.ui_data.upper() == 'all':
        # 如果select是多选
        if select.is_multiple:
            for i in range(len(select.options)):
                select.select_by_index(i)
        else:
            raise ValueError('单项选择框不允许全选')
    # 尝试把data转为json对象
    else:
        try:
            option_list = json.loads(vic_step.ui_data)
        except json.JSONDecodeError:
            raise ValueError('无法解析的选项表达式！请检查表达式，注意是否符合json字符串规范。')
        if not select.is_multiple and len(option_list) > 1:
            raise ValueError('单项选择框不允许多选')
        for option in option_list:
            if 'all' in option and option['all']:
                # 如果select是多选
                if select.is_multiple:
                    for i in range(len(select.options)):
                        select.select_by_index(i)
                else:
                    raise ValueError('单项选择框不允许全选')
                break
            else:
                try:
                    if option['select_by'] == 'value':
                        select.select_by_value(str(option['select_value']))
                    elif option['select_by'] == 'text':
                        select.select_by_visible_text(str(option['select_value']))
                    elif option['select_by'] == 'index':
                        select.select_by_index(int(option['select_value']))
                    else:
                        raise ValueError('无法解析的选项表达式！请按照格式提供表达式。')
                except KeyError:
                    raise ValueError('无法解析的选项表达式！请按照格式提供表达式。')

    selected_text_list = list()
    [selected_text_list.append(_option.text) for _option in select.all_selected_options]

    run_result = ['p', '在元素{}中进行了选择操作，被选中的选项为【{}】'.format(el_msg, '|'.join(selected_text_list))]
    if print_:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, run_result[1]))
    return run_result, element, elapsed_time, pause_time


# 获取特殊键组合
def get_special_keys(data_, logger=logging.getLogger('py_test')):
    data_ = data_.replace('\\+', '#{#plus#}#')
    data_list = data_.split('+')
    keys = []
    from selenium.webdriver.common.keys import Keys
    for key_str in data_list:
        key_str = key_str.replace('#{#plus#}#', '+').replace('\\$', '#{#dollar#}#')
        if key_str.find('$') == 0 and len(key_str) > 1:
            key_str = key_str.replace('#{#dollar#}#', '$')
            key_name = key_str.replace('$', '', 1).upper()
            if key_name == '\\N':
                key_str = '\n'
            elif key_name == '\\R':
                key_str = '\r'
            else:
                try:
                    key_str = getattr(Keys, key_name)
                except AttributeError:
                    logger.warning('【{}】不是一个合法的特殊键，已忽略'.format(key_str))
        else:
            key_name = key_str = key_str.replace('#{#dollar#}#', '$')
        keys.append((key_str, key_name))
    return keys


# 特殊动作
def perform_special_action(vic_step, print_=True):
    elapsed_time = 0
    pause_time = 0
    if not vic_step.ui_by or not vic_step.ui_locator:
        element = None
        el_msg = "【当前鼠标位置】"
    else:
        element, el_msg, _, elapsed_time, pause_time = get_element(vic_step, print_=print_, necessary=True)

    dr = vic_step.drs['web_dr']
    sp = vic_step.ui_special_action

    log_prefix = f"【{vic_step.execute_str}】\t"
    msg = '特殊动作执行完毕'

    if sp == 'click':
        ActionChains(dr).click(element).perform()
        vic_step.logger.info(f"{log_prefix}在{el_msg}执行左键单击操作")

    elif sp == 'double_click':
        ActionChains(dr).double_click(element).perform()
        vic_step.logger.info(f"{log_prefix}在{el_msg}执行左键双击操作")

    elif sp == 'context_click':
        ActionChains(dr).context_click(element).perform()
        vic_step.logger.info(f"{log_prefix}在{el_msg}执行右键单击操作")

    elif sp == 'click_and_hold':
        ActionChains(dr).click_and_hold(element).perform()
        vic_step.logger.info(f"{log_prefix}在{el_msg}执行左键点按操作")

    elif sp == 'release':
        ActionChains(dr).release(element).perform()
        vic_step.logger.info(f"{log_prefix}在{el_msg}执行鼠标双击操作")

    elif sp == 'move_by_offset':
        data = vic_step.ui_data.split(',')
        if len(data) < 2:
            raise ValueError('必须指定一组偏移坐标')
        xoffset = int(convert_string_to_float(data[0].strip(), _raise=True))
        yoffset = int(convert_string_to_float(data[1].strip(), _raise=True))
        ActionChains(dr).move_by_offset(xoffset, yoffset).perform()
        vic_step.logger.info(f"{log_prefix}执行移动鼠标到偏移点位置操作")

    elif sp == 'move_to_element':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个元素')
        ActionChains(dr).move_to_element(element).perform()
        vic_step.logger.info(f"{log_prefix}执行移动鼠标到{el_msg}元素操作")

    elif sp == 'move_to_element_with_offset':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个元素')
        data = vic_step.ui_data.split(',')
        if len(data) < 2:
            raise ValueError('必须指定一组偏移坐标')
        xoffset = int(convert_string_to_float(data[0].strip(), _raise=True))
        yoffset = int(convert_string_to_float(data[1].strip(), _raise=True))
        ActionChains(dr).move_to_element_with_offset(element, xoffset, yoffset).perform()
        vic_step.logger.info(f"{log_prefix}执行移动鼠标到以{el_msg}元素左上角为基准的偏移点位置操作")

    elif sp == 'drag_and_drop':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个元素')
        target_element = vic_variables.get_elements(vic_step.ui_data, vic_step.variables, vic_step.global_variables)[0]
        if not isinstance(target_element, WebElement):
            raise ValueError('必须指定一个目标元素')
        ActionChains(dr).drag_and_drop(element, target_element).perform()
        vic_step.logger.info(f"{log_prefix}执行拖动{el_msg}元素到另一元素上操作")

    elif sp == 'drag_and_drop_by_offset':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个元素')
        data = vic_step.ui_data.split(',')
        if len(data) < 2:
            raise ValueError('必须指定一组目标坐标')
        xoffset = int(convert_string_to_float(data[0].strip(), _raise=True))
        yoffset = int(convert_string_to_float(data[1].strip(), _raise=True))
        ActionChains(dr).drag_and_drop_by_offset(element, xoffset, yoffset).perform()
        vic_step.logger.info(f"{log_prefix}执行拖动{el_msg}元素到偏移点位置操作")

    elif sp == 'scroll_by_amount':
        data = vic_step.ui_data.split(',')
        if len(data) < 2:
            raise ValueError('必须指定一组偏移坐标')
        xoffset = int(convert_string_to_float(data[0].strip(), _raise=True))
        yoffset = int(convert_string_to_float(data[1].strip(), _raise=True))
        ActionChains(dr).scroll_by_amount(xoffset, yoffset).perform()
        vic_step.logger.info(f"{log_prefix}执行滚动到偏移点位置操作")

    elif sp == 'scroll_to_element':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个元素')
        ActionChains(dr).scroll_to_element(element).perform()
        vic_step.logger.info(f"{log_prefix}执行滚动到{el_msg}元素底部操作")

    elif sp == 'key_down':
        keys = get_special_keys(vic_step.ui_data, logger=vic_step.logger)
        ActionChains(dr).key_down(keys[0][0], element).perform()
        el_msg = "【当前焦点元素】" if not element else el_msg
        vic_step.logger.info(f"{log_prefix}在{el_msg}按住【{keys[0][1]}】")

    elif sp == 'key_up':
        keys = get_special_keys(vic_step.ui_data, logger=vic_step.logger)
        ActionChains(dr).key_up(keys[0][0], element).perform()
        el_msg = "【当前焦点元素】" if not element else el_msg
        vic_step.logger.info(f"{log_prefix}在{el_msg}释放【{keys[0][1]}】")

    elif sp == 'send_keys':
        el_msg = "【当前焦点元素】" if not element else el_msg
        vic_step.logger.info(f"{log_prefix}在{el_msg}进行下列键盘操作")
        keys = get_special_keys(vic_step.ui_data, logger=vic_step.logger)
        modifier_keys = {"\ue008": [0, "SHIFT"], "\ue009": [0, "CONTROL"], "\ue010": [0, "ALT"]}  # 考虑多个键使用相同的值，例如SHIFT和LEFT_SHIFT
        for key_str, key_name in keys:
            if key_str in modifier_keys:
                if modifier_keys[key_str][0] == 0:
                    modifier_keys[key_str][0] = 1
                    ActionChains(dr).key_down(key_str, element).perform()
                    vic_step.logger.info(f"{log_prefix}按住【{key_name}】")
                else:
                    modifier_keys[key_str][0] = 0
                    ActionChains(dr).key_up(key_str, element).perform()
                    vic_step.logger.info(f"{log_prefix}释放【{key_name}】")
            else:
                if element:
                    ActionChains(dr).send_keys_to_element(element, key_str).perform()
                else:
                    ActionChains(dr).send_keys(key_str).perform()
                vic_step.logger.info(f"{log_prefix}按【{key_name}】")
        for k, v in modifier_keys.items():
            if v[0] != 0:
                ActionChains(dr).key_up(k, element).perform()
                vic_step.logger.info(f"{log_prefix}自动释放【{v[1]}】")
    else:
        raise ValueError('无法处理的特殊操作[{}]'.format(sp))

    run_result = ['p', msg]
    if print_:
        vic_step.logger.info(f"{log_prefix}{run_result[1]}")
    return run_result, element, elapsed_time, pause_time


# 尝试滚动到元素位置
def try_to_scroll_into_view(vic_step, print_=True):
    element, el_msg, _, elapsed_time, pause_time = get_element(vic_step, print_=print_)
    highlight_for_a_moment(vic_step.drs['web_dr'], (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    vic_step.drs['web_dr'].execute_script('arguments[0].scrollIntoView()', element)
    run_result = ['p', '移动窗口到元素{}的位置'.format(el_msg)]
    if print_:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, run_result[1]))
    return run_result, element, elapsed_time, pause_time


# 处理浏览器弹窗
def alert_handle(vic_step, print_=True):
    pause_time = 0
    _success = False
    _full_msg = ''
    msg = 'N/A'
    msg_format = '经过{:.1f}秒 - {}'
    alert_text = ''
    dr = vic_step.drs['web_dr']
    last_print_time = start_time = time.time()
    while (time.time() - start_time - pause_time) <= vic_step.timeout and not vic_step.force_stop:
        try:
            alert_ = dr.switch_to.alert
            alert_text = alert_.text
            if vic_step.ui_alert_handle == 'dismiss':
                alert_.dismiss()
                msg = '点击【取消】按钮关闭弹窗，弹窗内容：{}'.format(alert_text)
            else:
                _msg = ''
                if vic_step.ui_alert_handle_text:
                    alert_.send_keys(vic_step.ui_alert_handle_text)
                    _msg = '输入【{}】，'.format(vic_step.ui_alert_handle_text)
                alert_.accept()
                msg = '{}点击【确定】按钮关闭弹窗，弹窗内容：{}'.format(_msg, alert_text)
            _success = True
        except exceptions.NoAlertPresentException:
            msg = '找不到任何浏览器弹窗'

        if time.time() - last_print_time >= 1:
            pause_time += vic_step.pause_()
            elapsed_time = time.time() - start_time - pause_time
            _full_msg = msg_format.format(elapsed_time, msg)
            if print_:
                vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, _full_msg))
            last_print_time = time.time()

        if _success:
            break

    elapsed_time = time.time() - start_time - pause_time
    full_msg = msg_format.format(elapsed_time, msg)
    if print_ and full_msg != _full_msg:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, full_msg))
    if _success:
        run_result = ['p', full_msg]
    else:
        raise exceptions.NoAlertPresentException(full_msg)
    return run_result, alert_text, elapsed_time, pause_time


# 尝试切换窗口
def try_to_switch_to_window(vic_step, current_window_handle=None, print_=True):
    pause_time = 0
    _success = False
    _full_msg = ''
    msg = '无法切换到符合条件的窗口'
    msg_format = '经过{:.1f}秒 - {}'
    new_window_handle = None
    if not current_window_handle:
        try:
            current_window_handle = vic_step.drs['web_dr'].current_window_handle
        except exceptions.NoSuchWindowException:
            vic_step.logger.warning('【{}】\t无法获取当前窗口'.format(vic_step.execute_str), exc_info=True)
            current_window_handle = 'N/A'
    last_print_time = start_time = time.time()
    while (time.time() - start_time - pause_time) <= vic_step.timeout and not vic_step.force_stop:
        for window_handle in vic_step.drs['web_dr'].window_handles:
            if window_handle != current_window_handle:
                vic_step.drs['web_dr'].switch_to.window(window_handle)
                # 如果定位信息不全，且没有ui_data，则直接切换到这个窗口
                if (not vic_step.ui_by or not vic_step.ui_locator) and not vic_step.ui_data:
                    new_window_handle = window_handle
                    msg = '切换到新窗口'
                    _success = True
                    break
                elif vic_step.ui_data:  # 如果定位信息不全，但提供了ui_data，则把ui_data视为窗口标题
                    vic_step.ui_by = 'xpath'
                    vic_step.ui_locator = '/html/head/title[contains(text(), "{}")]'.format(vic_step.ui_data)
                    vic_step.variable_elements = None
                    vic_step.ui_base_element = None
                    _msg = '标题为{}的窗口'.format(vic_step.ui_data)
                else:  # 否则使用定位信息查找元素
                    _msg = '包含元素【By:{}|Locator:{}】的窗口'.format(vic_step.ui_by, vic_step.ui_locator)

                run_result_temp, elements, _elapsed_time, _pause_time = wait_for_element_present(
                    vic_step, timeout=1, print_=False)
                pause_time += _pause_time
                if elements and ((not vic_step.ui_index and len(elements) == 1)
                                 or (vic_step.ui_index and vic_step.ui_index <= len(elements)-1)):
                    new_window_handle = window_handle
                    msg = '切换到{}'.format(_msg)
                    _success = True
                    break
                else:
                    msg = '无法切换到{}'.format(_msg)

        if time.time() - last_print_time >= 1:
            pause_time += vic_step.pause_()
            elapsed_time = time.time() - start_time - pause_time
            _full_msg = msg_format.format(elapsed_time, msg)
            if print_:
                vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, _full_msg))
            last_print_time = time.time()

        if _success:
            break

    elapsed_time = time.time() - start_time - pause_time
    full_msg = msg_format.format(elapsed_time, msg)
    if print_ and full_msg != _full_msg:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, full_msg))
    if _success:
        run_result = ['p', full_msg]
    else:
        raise exceptions.NoSuchWindowException(full_msg)
    return run_result, new_window_handle, elapsed_time, pause_time


# 尝试切换框架
def try_to_switch_to_frame(vic_step, print_=True):
    pause_time = 0
    _success = False
    _full_msg = ''
    msg = '未能切换到指定的框架'
    msg_format = '经过{:.1f}秒 - {}'
    last_print_time = start_time = time.time()
    while (time.time() - start_time - pause_time) <= vic_step.timeout and not vic_step.force_stop:
        if vic_step.ui_by and vic_step.ui_locator:
            frame, el_msg, err_msg, _, _pause_time = get_element(
                vic_step, timeout=1, print_=False, necessary=False)
            pause_time += _pause_time
            if frame:
                vic_step.drs['web_dr'].switch_to.frame(frame)
                _success = True
                msg = '切换到元素{}对应的框架'.format(el_msg)
            else:
                msg = '未能切换到元素对应的框架，因为{}'.format(err_msg)
        else:
            index_ = vic_step.ui_index if vic_step.ui_index else 0
            try:
                vic_step.drs['web_dr'].switch_to.frame(index_)
                _success = True
                msg = '已切换到索引为{}的框架'.format(index_)
            except exceptions.NoSuchFrameException:
                msg = '未能切换到索引为{}的框架'.format(index_)

        if time.time() - last_print_time >= 1:
            pause_time += vic_step.pause_()
            elapsed_time = time.time() - start_time - pause_time
            _full_msg = msg_format.format(elapsed_time, msg)
            if print_:
                vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, _full_msg))
            last_print_time = time.time()

        if _success:
            break

    elapsed_time = time.time() - start_time - pause_time
    full_msg = msg_format.format(elapsed_time, msg)
    if print_ and full_msg != _full_msg:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, full_msg))
    if _success:
        run_result = ['p', full_msg]
    else:
        raise exceptions.NoSuchFrameException(full_msg)
    return run_result, elapsed_time, pause_time


# 运行javascript
def run_js(vic_step, print_=True):
    elapsed_time = 0
    pause_time = 0
    if vic_step.ui_by in (None, ''):
        js_result = vic_step.drs['web_dr'].execute_script(vic_step.ui_data)
    else:
        if vic_step.variable_elements:
            elements = vic_step.variable_elements
        else:
            run_result_temp, elements, elapsed_time, pause_time = wait_for_element_present(vic_step, print_=print_)
            if run_result_temp[0] == 'f':
                raise exceptions.NoSuchElementException(run_result_temp[1])
        if vic_step.ui_index is None:
            js_result = vic_step.drs['web_dr'].execute_script(vic_step.ui_data, elements)
        elif vic_step.ui_index > (len(elements) - 1):
            raise ValueError('找到{}个元素，但指定的索引【{}】超出可用范围（0到{}）'.format(
                len(elements), vic_step.ui_index, len(elements) - 1))
        else:
            js_result = vic_step.drs['web_dr'].execute_script(vic_step.ui_data, elements[vic_step.ui_index])
    if isinstance(js_result, WebElement):
        js_result = [js_result]
    run_result = ['p', 'JavaScript执行完毕，返回值为：\n{}'.format(js_result)]
    if print_:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, run_result[1]))
    return run_result, js_result, elapsed_time, pause_time


# 获取元素文本
def get_element_text(vic_step, print_=True):
    element, el_msg, _, elapsed_time, pause_time = get_element(vic_step, print_=print_)
    highlight_for_a_moment(vic_step.drs['web_dr'], (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    text = element.text
    run_result = ['p', '获取了元素{}的文本：{}'.format(el_msg, text)]
    if print_:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, run_result[1]))
    return run_result, text, elapsed_time, pause_time


# 获取元素属性
def get_element_attr(vic_step, print_=True):
    element, el_msg, _, elapsed_time, pause_time = get_element(vic_step, print_=print_)
    highlight_for_a_moment(vic_step.drs['web_dr'], [element], 'outline: 2px dotted yellow; border: 1px solid yellow;')
    attr = element.get_attribute(vic_step.ui_data)
    if attr:
        run_result = ['p', '获取了元素{}的【{}】属性值：{}'.format(el_msg, vic_step.ui_data, attr)]
    else:
        run_result = ['f', '元素{}不存在【{}】属性'.format(el_msg, vic_step.ui_data)]
    if print_:
        vic_step.logger.info('【{}】\t{}'.format(vic_step.execute_str, run_result[1]))
    return run_result, attr, elapsed_time, pause_time


if __name__ == '__main__':
    from typing import Iterable
    from typing import List
    from typing import Optional
    from typing import Union
    from selenium.types import AnyKey
    from selenium.webdriver.common.keys import Keys


    def send_keys(*keys_to_send: str):
        """Sends keys to current focused element.

        :Args:
         - keys_to_send: The keys to send.  Modifier keys constants can be found in the
           'Keys' class.
        """
        typing = keys_to_typing(keys_to_send)
        print(typing)


    def keys_to_typing(value: Iterable[AnyKey]) -> List[str]:
        """Processes the values that will be typed in the element."""
        characters: List[str] = []
        for val in value:
            if isinstance(val, Keys):
                # Todo: Does this even work?
                characters.append(val)
            elif isinstance(val, (int, float)):
                characters.extend(str(val))
            else:
                characters.extend(val)
        return characters


    _ = get_special_keys("$CONTROL+a+$CONTROL+$BACKSPACE+Abc")
    print(_)
    send_keys(_)
