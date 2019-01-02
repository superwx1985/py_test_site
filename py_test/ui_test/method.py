import time
import json
import logging
from selenium.common import exceptions
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.action_chains import ActionChains
from py_test.vic_tools import vic_find_object, vic_eval
from py_test.vic_tools.vic_str_handle import change_string_to_digit
from py_test.general import vic_variables


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
            '''var element = arguments[0];
            var original_style = element.getAttribute("style")?element.getAttribute("style"):"";
            element.setAttribute("style", original_style + "; ''' + style + '''");
            return original_style;''', element)
        highlight_elements_map[element] = original_style
    return highlight_elements_map


# 元素取消高亮
def cancel_highlight(dr, elements_map):
    for element, original_style in elements_map.items():
        try:
            dr.execute_script(
                '''var element = arguments[0];
                var original_style = arguments[1];
                element.setAttribute("style", original_style + ";");''',
                element, original_style)
        except exceptions.StaleElementReferenceException:
            pass  # 如果元素此时已被刷新，则忽略本操作


# 元素高亮N秒
def highlight_for_a_moment(dr, elements, color='green', duration=0.5):
    # background-color: rgba(255, 0, 0, 0.7)
    style = 'outline: 2px dotted %s; border: 1px solid %s;' % (color, color)
    for element in elements:
        dr.execute_script(
            '''var element = arguments[0];
            var original_style = element.getAttribute("style")?element.getAttribute("style"):"";
            element.setAttribute("style", original_style + "; ''' + style + '''");
            setTimeout(function(){element.setAttribute("style", original_style);}, ''' + str(
                round(duration * 1000)) + ');', element)
    time.sleep(0.5)


# 等待文字出现
def wait_for_text_present(vic_step, print_=True):
    start_time = time.time()
    last_print_time = 0
    elements = list()
    fail_elements = list()
    index_ = vic_step.ui_index
    text = vic_step.ui_data
    run_result = ['f', 'N/A']
    _success = False
    msg = '没找到期望文字【{}】'.format(text)
    vic_step.dr.implicitly_wait(0.5)
    while (time.time() - start_time) <= vic_step.timeout:
        elements.clear()
        fail_elements.clear()
        if not vic_step.ui_by and not vic_step.ui_locator:
            _body = vic_step.dr.find_element_by_tag_name('body')
            find_result = vic_find_object.find_with_condition(text, _body.text, logger=vic_step.logger)
            if find_result.is_matched:
                elements_temp = vic_step.dr.find_elements_by_xpath('//body//*[contains(text(),"' + text + '")]')
                for element in elements_temp:
                    if element.is_displayed():
                        elements.append(element)
                if not elements:  # 如果文本不在元素的第一个子节点，用text()可能会找不到
                    elements.append(_body)
                msg = '在页面找到期望文字【{}】'.format(text)
                _success = True
        else:
            _ui_data = vic_step.ui_data  # 把ui_data置空，防止查找元素时被当做数量限制表达式
            vic_step.ui_data = None
            run_result_temp, elements_temp, elements_all = wait_for_element_visible(vic_step, timeout=1, print_=False)
            vic_step.ui_data = _ui_data
            if run_result_temp[0] == 'f':
                msg = '未找到期望元素【By:{}|Locator:{}】或元素不可见'.format(vic_step.ui_by, vic_step.ui_locator)
            else:
                if index_ is None:
                    for element_temp in elements_temp:
                        element_text = vic_step.dr.execute_script(
                            'return arguments[0].textContent||arguments[0].innerText||arguments[0].value',
                            element_temp)
                        find_result = vic_find_object.find_with_condition(text, element_text, logger=vic_step.logger)
                        if find_result.is_matched:
                            elements.append(element_temp)
                        else:
                            fail_elements.append(element_temp)
                elif index_ > (len(elements_temp) - 1):
                    raise ValueError('找到{}个元素，但指定的index【{}】超出可用范围（0到{}）'.format(
                        len(elements), index_, len(elements) - 1))
                else:
                    element_text = vic_step.dr.execute_script(
                        'return arguments[0].textContent||arguments[0].innerText||arguments[0].value',
                        elements_temp[index_])
                    find_result = vic_find_object.find_with_condition(text, element_text, logger=vic_step.logger)
                    if find_result.is_matched:
                        elements.append(elements_temp[index_])
                    else:
                        fail_elements.append(elements_temp[index_])
                msg = '找到期望元素【By:{}|Locator:{}】{}个，其中有{}个元素包含期望文字【{}】'.format(
                    vic_step.ui_by, vic_step.ui_locator, len(elements_temp), len(elements), text)
            if elements and not fail_elements:
                _success = True

        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            msg = '经过{}秒 - {}'.format(elapsed_time, msg)
            vic_step.logger.info(msg)
            last_print_time = now_time

        if _success:
            run_result = ['p', msg]
            break
        else:
            run_result = ['f', msg]

    vic_step.dr.implicitly_wait(vic_step.timeout)
    return run_result, elements, fail_elements


# 等待元素出现
def wait_for_element_present(vic_step, timeout=None, print_=True):
    elements = list()
    if not timeout:
        timeout = vic_step.timeout

    vic_step.dr.implicitly_wait(0.5)
    start_time = time.time()
    last_print_time = 0
    while (time.time() - start_time) <= timeout:
        if vic_step.variable_elements:
            elements = vic_step.variable_elements
        else:
            if isinstance(vic_step.ui_base_element, WebElement):
                elements = vic_step.ui_base_element.find_elements(vic_step.ui_by, vic_step.ui_locator)
            else:
                elements = vic_step.dr.find_elements(vic_step.ui_by, vic_step.ui_locator)
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            vic_step.logger.info('经过{}秒 - 找到期望元素{}个'.format(elapsed_time, len(elements)))
            last_print_time = now_time
        if elements:
            break
    vic_step.dr.implicitly_wait(timeout)
    elapsed_time = str(round(time.time() - start_time, 2))
    msg = '经过{}秒 - 找到期望元素【By:{}|Locator:{}】{}个'.format(elapsed_time, vic_step.ui_by, vic_step.ui_locator, len(elements))
    if elements:
        run_result = ['p', msg]
    else:
        run_result = ['f', msg]
    return run_result, elements


# 获取元素
def get_element(vic_step, timeout=None, print_=True, necessary=True):
    if not timeout:
        timeout = vic_step.timeout
    result_msg = '未找到'
    el_msg = '符合条件的元素'
    element = None
    last_print_time = 0
    start_time = time.time()
    while (time.time() - start_time) <= timeout:
        run_result_temp, elements = wait_for_element_present(vic_step, timeout=1, print_=print_)
        if run_result_temp[0] == 'p':
            result_msg = '找到'
            if vic_step.ui_index:
                if vic_step.ui_index > (len(elements) - 1):
                    el_msg = '{}个元素，但指定的index【{}】超出可用范围（0到{}）'.format(
                        len(elements), vic_step.ui_index, len(elements) - 1)
                else:
                    element = elements[vic_step.ui_index]
                    el_msg = '元素【By:{}|Locator:{}|Index:{}】'.format(
                        vic_step.ui_by, vic_step.ui_locator, vic_step.ui_index)
            else:
                if len(elements) > 1:
                    el_msg = '{}个元素，请指定一个index'.format(len(elements))
                else:
                    element = elements[0]
                    el_msg = '元素【By:{}|Locator:{}】'.format(vic_step.ui_by, vic_step.ui_locator)
        else:
            result_msg = '未找到'
            el_msg = '符合条件的元素'
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            vic_step.logger.info('经过{}秒 - {}{}'.format(elapsed_time, result_msg, el_msg))
            last_print_time = now_time
        if element:
            break
    if necessary and not element:
        raise exceptions.NoSuchElementException('{}{}'.format(result_msg, el_msg))
    return element, result_msg, el_msg


# 等待元素可见
def wait_for_element_visible(vic_step, timeout=None, print_=True):
    elements = list()
    visible_elements = list()
    if not timeout:
        timeout = vic_step.timeout
    run_result = ['f', 'N/A']
    _success = False
    vic_step.dr.implicitly_wait(0.5)
    last_print_time = 0
    start_time = time.time()
    while (time.time() - start_time) <= timeout:
        visible_elements.clear()
        if vic_step.variable_elements:
            elements = vic_step.variable_elements
        else:
            if isinstance(vic_step.ui_base_element, WebElement):
                elements = vic_step.ui_base_element.find_elements(vic_step.ui_by, vic_step.ui_locator)
            else:
                elements = vic_step.dr.find_elements(vic_step.ui_by, vic_step.ui_locator)
        if elements:
            for element in elements:
                if element.is_displayed():
                    visible_elements.append(element)

        msg = '找到期望元素【By:{}|Locator:{}】{}个，其中可见元素{}个'.format(
            vic_step.ui_by, vic_step.ui_locator, len(elements), len(visible_elements))
        if visible_elements:
            if vic_step.ui_data:
                eo = vic_eval.EvalObject(vic_step.ui_data, {'x': len(visible_elements)}, vic_step.logger)
                eval_success, eval_result, final_expression = eo.get_eval_result()
                compare_result = eval_result
                if compare_result is True:
                    msg = '{}，符合给定的数量限制'.format(msg)
                    _success = True
                else:
                    msg = '{}，不符合给定的数量限制'.format(msg)
            else:
                _success = True

        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            msg = '经过{}秒 - {}'.format(elapsed_time, msg)
            vic_step.logger.info(msg)
            last_print_time = now_time

        if _success:
            run_result = ['p', msg]
            break
        else:
            run_result = ['f', msg]

    vic_step.dr.implicitly_wait(timeout)
    return run_result, visible_elements, elements


# 获取可见元素
def get_variable_element(vic_step, timeout=None, print_=True):
    if not timeout:
        timeout = vic_step.timeout
    _ui_data = vic_step.ui_data  # 把ui_data置空，防止查找元素时被当做数量限制表达式
    vic_step.ui_data = None
    run_result_temp, elements, _ = wait_for_element_visible(vic_step, timeout=timeout, print_=print_)
    vic_step.ui_data = _ui_data
    if run_result_temp[0] == 'f':
        raise exceptions.NoSuchElementException('未找到指定的元素，{}'.format(run_result_temp[1]))
    elif len(elements) == 1 and vic_step.ui_index in (None, 0):
        element = elements[0]
    elif vic_step.ui_index is None:
        raise ValueError('找到{}个元素，请指定一个index'.format(len(elements)))
    elif vic_step.ui_index > (len(elements) - 1):
        raise ValueError('找到{}个元素，但指定的index【{}】超出可用范围（0到{}）'.format(
            len(elements), vic_step.ui_index, len(elements) - 1))
    else:
        element = elements[vic_step.ui_index]
    return element


# 等待元素消失
def wait_for_element_disappear(vic_step, print_=True):
    visible_elements = list()
    elements = list()
    vic_step.dr.implicitly_wait(0.5)
    last_print_time = 0
    start_time = time.time()
    while (time.time() - start_time) <= vic_step.timeout:
        visible_elements = list()
        if vic_step.variable_elements:
            elements = vic_step.variable_elements
        else:
            if isinstance(vic_step.ui_base_element, WebElement):
                elements = vic_step.ui_base_element.find_elements(vic_step.ui_by, vic_step.ui_locator)
            else:
                elements = vic_step.dr.find_elements(vic_step.ui_by, vic_step.ui_locator)
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            vic_step.logger.info('经过{}秒 - 找到期望元素{}个，其中可见元素{}个'.format(
                elapsed_time, len(elements), len(visible_elements)))
            last_print_time = now_time
        if not elements:
            break
        else:
            for element in elements:
                if element.is_displayed():
                    visible_elements.append(element)
            if len(visible_elements) == 0:
                break
        vic_step.dr.implicitly_wait(vic_step.timeout)
    elapsed_time = str(round(time.time() - start_time, 2))
    msg = '经过{}秒 - 找到期望元素【By:{}|Locator:{}】{}个，其中可见元素{}个'.format(
        vic_step.ui_by, vic_step.ui_locator, elapsed_time, len(elements), len(visible_elements))
    if not visible_elements:
        run_result = ['p', msg]
    else:
        run_result = ['f', msg]
    return run_result, visible_elements


# 跳转到url
def go_to_url(vic_step):
    url = vic_step.ui_data
    vic_step.dr.get(url)
    run_result = ['p', '成功打开URL【{}】'.format(url)]
    return run_result


# 等待页面跳转
def wait_for_page_redirect(vic_step, print_=True):
    is_passed = False
    start_time = time.time()
    last_print_time = 0
    while (time.time() - start_time) <= vic_step.timeout:
        current_url = vic_step.dr.current_url
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            vic_step.logger.info('经过%s秒 - 验证新URL是否符合期望' % elapsed_time)
            last_print_time = now_time
        find_result = vic_find_object.find_with_condition(vic_step.ui_data, current_url, logger=vic_step.logger)
        if find_result.is_matched:
            is_passed = True
            break
    elapsed_time = str(round(time.time() - start_time, 2))
    if not is_passed:
        run_result = ['f', '经过{}秒 - 新URL不符合期望【{}】'.format(elapsed_time, vic_step.ui_data)]
    else:
        run_result = ['p', '经过{}秒 - 新URL符合期望【{}】'.format(elapsed_time, vic_step.ui_data)]
    return run_result


# 获取URL
def get_url(vic_step):
    url = vic_step.dr.current_url
    condition_value = vic_step.ui_data

    if condition_value:
        find_result = vic_find_object.find_with_condition(condition_value, url, logger=vic_step.logger)
        if find_result.is_matched:
            if find_result.re_result:
                url = find_result.re_result[0]
            run_result = ['p', '找到符合条件【{}】的URL内容【{}】'.format(condition_value, url)]
        else:
            run_result = ['f', '找不到符合条件【{}】的URL内容'.format(condition_value)]
    else:
        run_result = ['p', '获取到URL【{}】'.format(url)]
    return run_result, url


# 尝试点击
def try_to_click(vic_step, print_=True):
    element = get_variable_element(vic_step, print_=print_)

    highlight_for_a_moment(vic_step.dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    element.click()
    run_result = ['p', '点击元素【By:{}|Locator:{}】'.format(vic_step.ui_by, vic_step.ui_locator)]
    return run_result, element


# 尝试输入
def try_to_enter(vic_step, print_=True):
    element = get_variable_element(vic_step, print_=print_)

    highlight_for_a_moment(vic_step.dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    element.clear()
    element.send_keys(vic_step.ui_data)
    run_result = ['p', '在元素【By:{}|Locator:{}】中输入【{}】'.format(vic_step.ui_by, vic_step.ui_locator, vic_step.ui_data)]
    return run_result, element


# 尝试选择
def try_to_select(vic_step, print_=True):
    element = get_variable_element(vic_step, print_=print_)

    highlight_for_a_moment(vic_step.dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
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

    run_result = [
        'p', '在元素【By:{}|Locator:{}】中进行了选择操作，被选中的选项为【{}】'.format(
            vic_step.ui_by, vic_step.ui_locator, '|'.join(selected_text_list))
    ]
    return run_result, element


# 获取特殊键组合
def get_special_keys(data_, logger=logging.getLogger('py_test')):
    data_ = data_.replace('\\+', '#{#plus#}#')
    data_list = data_.split('+')
    keys = list()
    from selenium.webdriver.common.keys import Keys
    for key_str in data_list:
        key_str = key_str.replace('#{#plus#}#', '+').replace('\\$', '#{#dollar#}#')
        if key_str.find('$') == 0 and len(key_str) > 1:
            key_str = key_str.replace('#{#dollar#}#', '$')
            try:
                key_str = getattr(Keys, key_str.replace('$', '', 1).upper())
            except AttributeError:
                logger.warning('【{}】不是一个合法的特殊键，不进行转换'.format(key_str))
            keys.append(key_str)
        else:
            key_str = key_str.replace('#{#dollar#}#', '$')
            keys.append(key_str)
    return keys


# 特殊动作
def perform_special_action(vic_step, print_=True):
    if not vic_step.ui_by or not vic_step.ui_locator:
        element = None
    else:
        element = get_variable_element(vic_step, print_=print_)

    dr = vic_step.dr
    sp = vic_step.ui_special_action

    if sp == 'click':
        ActionChains(dr).click(element).perform()

    elif sp == 'click_and_hold':
        ActionChains(dr).click_and_hold(element).perform()

    elif sp == 'context_click':
        ActionChains(dr).context_click(element).perform()

    elif sp == 'double_click':
        ActionChains(dr).double_click(element).perform()

    elif sp == 'release':
        ActionChains(dr).release(element).perform()

    elif sp == 'move_by_offset':
        data = vic_step.ui_data.split(',')
        if len(data) < 2:
            raise ValueError('必须指定一组偏移坐标')
        xoffset = change_string_to_digit(data[0].strip())
        yoffset = change_string_to_digit(data[1].strip())
        ActionChains(dr).move_by_offset(xoffset, yoffset).perform()

    elif sp == 'move_to_element':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个元素')
        ActionChains(dr).move_to_element(element).perform()

    elif sp == 'move_to_element_with_offset':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个元素')
        data = vic_step.ui_data.split(',')
        if len(data) < 2:
            raise ValueError('必须指定一组偏移坐标')
        xoffset = change_string_to_digit(data[0].strip())
        yoffset = change_string_to_digit(data[1].strip())
        ActionChains(dr).move_to_element_with_offset(element, xoffset, yoffset).perform()

    elif sp == 'drag_and_drop':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个元素')
        target_element = vic_variables.get_elements(vic_step.ui_data, vic_step.variables, vic_step.global_variables)[0]
        if not isinstance(target_element, WebElement):
            raise ValueError('必须指定一个目标元素')
        ActionChains(dr).drag_and_drop(element, target_element).perform()

    elif sp == 'drag_and_drop_by_offset':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个元素')
        data = vic_step.ui_data.split(',')
        if len(data) < 2:
            raise ValueError('必须指定一组目标坐标')
        xoffset = change_string_to_digit(data[0].strip())
        yoffset = change_string_to_digit(data[1].strip())
        ActionChains(dr).drag_and_drop_by_offset(element, xoffset, yoffset).perform()

    elif sp == 'key_down':
        ActionChains(dr).key_down(element).perform()

    elif sp == 'key_up':
        ActionChains(dr).key_up(element).perform()

    elif sp == 'send_keys':
        keys = get_special_keys(vic_step.ui_data, logger=vic_step.logger)
        ActionChains(dr).send_keys(keys).perform()

    elif sp == 'send_keys_to_element':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个被操作元素')
        keys = get_special_keys(vic_step.ui_data, logger=vic_step.logger)
        ActionChains(dr).send_keys_to_element(element, keys).perform()

    else:
        raise ValueError('无法处理的特殊操作[{}]'.format(sp))

    run_result = ['p', '特殊动作执行完毕']
    return run_result, element


# 尝试滚动到元素位置
def try_to_scroll_into_view(vic_step, print_=True):
    element, _, _ = get_element(vic_step, print_=print_)
    highlight_for_a_moment(vic_step.dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    vic_step.dr.execute_script('arguments[0].scrollIntoView()', element)
    run_result = ['p', '移动窗口到元素【By:{}|Locator:{}】的位置'.format(vic_step.ui_by, vic_step.ui_locator)]
    return run_result, element


# 处理浏览器弹窗
def confirm_alert(dr, alert_handle, timeout, print_=True, logger=logging.getLogger('py_test')):
    start_time = time.time()
    last_print_time = 0
    done = False
    alert_handle_text = ''
    alert_text = ''
    while (time.time() - start_time) <= timeout:
        try:
            alert_ = dr.switch_to.alert
            alert_text = alert_.text
            if alert_handle.lower() in ('no', 'dismiss', 'cancel'):
                alert_.dismiss()
                alert_handle_text = '取消'
            elif alert_handle.lower() in ('skip', 'ignore'):
                alert_.ignore()
                alert_handle_text = '忽略'
            else:
                alert_.accept()
                alert_handle_text = '确定'
            done = True
            break
        except exceptions.NoAlertPresentException:
            pass
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            logger.info('经过%s秒 - 尝试以【%s】方式关闭弹窗' % (elapsed_time, alert_handle))
            last_print_time = now_time
    elapsed_time = str(round(time.time() - start_time, 2))
    if not done:
        raise exceptions.NoAlertPresentException('经过%s秒 - 找不到任何弹窗' % elapsed_time)
    return alert_handle_text, alert_text


# 尝试切换window或tap
def try_to_switch_to_window(vic_step, current_window_handle, print_=True):
    last_print_time = 0
    _success = False
    new_window_handle = None
    start_time = time.time()
    while (time.time() - start_time) <= vic_step.timeout:
        for window_handle in vic_step.dr.window_handles:
            if window_handle != current_window_handle:
                vic_step.dr.switch_to.window(window_handle)
                # 如果定位信息不全，且没有ui_data，则直接切换到这个窗口
                if (not vic_step.ui_by or not vic_step.ui_locator) and not vic_step.ui_data:
                    new_window_handle = window_handle
                    _success = True
                    break
                # 如果定位信息不全，但提供了ui_data，则把ui_data视为窗口标题
                elif vic_step.ui_data:
                    vic_step.ui_by = 'xpath'
                    vic_step.ui_locator = '/html/head/title[contains(text(), "{}")]'.format(vic_step.ui_data)
                    vic_step.variable_elements = None
                    vic_step.ui_base_element = None

                run_result_temp, elements = wait_for_element_present(vic_step, timeout=1, print_=False)

                if elements and ((not vic_step.ui_index and len(elements) == 1)
                                 or (vic_step.ui_index and vic_step.ui_index <= len(elements)-1)):
                    new_window_handle = window_handle
                    _success = True
                    break

        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            vic_step.logger.info('经过%s秒 - 尝试切换到新窗口' % elapsed_time)
            last_print_time = now_time
        if _success:
            break
    elapsed_time = str(round(time.time() - start_time, 2))
    if not _success:
        raise exceptions.NoSuchWindowException('经过%s秒 - 无法切换到新窗口或没找到指定的窗口' % elapsed_time)
    else:
        try:
            title = vic_step.dr.find_element_by_tag_name('title')
            title_str = title.get_attribute('innerText')  # selenium获取不可见元素的文本不能直接用text
        except exceptions.WebDriverException:
            title_str = '（无标题）'
        run_result = ['p', '经过{}秒 - 切换到新窗口【{}】'.format(elapsed_time, title_str)]
    return run_result, new_window_handle


# 尝试切换到框架
def try_to_switch_to_frame(vic_step, print_=True):
    start_time = time.time()
    last_print_time = 0
    success_ = False
    msg = '未能切换到符合条件的框架'
    while (time.time() - start_time) <= vic_step.timeout:
        if vic_step.ui_by and vic_step.ui_locator:
            frame, result_msg, el_msg = get_element(vic_step, timeout=1, print_=False, necessary=False)
            if frame:
                vic_step.dr.switch_to.frame(frame)
                success_ = True
                msg = '已切换到{}对应的框架'.format(el_msg)
            else:
                msg = '未能切换到指定元素对应的框架，因为：{}{}'.format(result_msg, el_msg)
        else:
            index_ = vic_step.ui_index if vic_step.ui_index else 0
            try:
                vic_step.dr.switch_to.frame(index_)
                success_ = True
                msg = '已切换到索引为{}的框架'.format(index_)
            except exceptions.NoSuchFrameException:
                msg = '未能切换到索引为{}的框架'.format(index_)
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            msg = '经过{}秒 - {}'.format(elapsed_time, msg)
            vic_step.logger.info(msg)
            last_print_time = now_time
        if success_:
            break
    if success_:
        run_result = ['p', msg]
    else:
        raise exceptions.NoSuchFrameException(msg)
    return run_result


# 运行javascript
def run_js(vic_step, print_=True):
    if vic_step.ui_by in (None, ''):
        js_result = vic_step.dr.execute_script(vic_step.ui_data)
    else:
        if vic_step.variable_elements:
            elements = vic_step.variable_elements
        else:
            run_result_temp, elements = wait_for_element_present(vic_step, print_=print_)
            if run_result_temp[0] == 'f':
                raise exceptions.NoSuchElementException(run_result_temp[1])
        if vic_step.ui_index is None:
            js_result = vic_step.dr.execute_script(vic_step.ui_data, elements)
        elif vic_step.ui_index > (len(elements) - 1):
            raise ValueError('找到{}个元素，但指定的index【{}】超出可用范围（0到{}）'.format(
                len(elements), vic_step.ui_index, len(elements) - 1))
        else:
            js_result = vic_step.dr.execute_script(vic_step.ui_data, elements[vic_step.ui_index])
    if isinstance(js_result, WebElement):
        js_result = [js_result]
    msg = 'JavaScript执行完毕，返回值为：\n{}'.format(js_result)
    if print_:
        vic_step.logger.info(msg)
    run_result = ['p', msg]
    return run_result, js_result


# 获取元素文本
def get_element_text(vic_step, print_=True):
    element, _, _ = get_element(vic_step, print_=print_)
    highlight_for_a_moment(vic_step.dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    text = element.text
    run_result = ['p', '元素【By:{}|Locator:{}】的文本为：{}'.format(vic_step.ui_by, vic_step.ui_locator, text)]
    return run_result, text


# 获取元素属性
def get_element_attr(vic_step, print_=True):
    element, _, _ = get_element(vic_step, print_=print_)
    highlight_for_a_moment(vic_step.dr, [element], 'outline: 2px dotted yellow; border: 1px solid yellow;')
    attr = element.get_attribute(vic_step.ui_data)
    if attr:
        run_result = ['p', '元素【By:{}|Locator:{}】的【{}】属性的值为：{}'.format(
            vic_step.ui_by, vic_step.ui_locator, vic_step.ui_data, attr)]
    else:
        run_result = ['f', '元素【By:{}|Locator:{}】不存在【{}】属性'.format(vic_step.ui_by, vic_step.ui_locator, vic_step.ui_data)]
    return run_result, attr


# 解析表达式
def analysis_expression(vic_step):
    eval_expression = vic_step.other_data
    variable_dict = vic_variables.get_variable_dict(vic_step.variables, vic_step.global_variables)
    logger = vic_step.logger
    eo = vic_eval.EvalObject(eval_expression, variable_dict, logger)
    eval_success, eval_result, final_expression = eo.get_eval_result()
    if eval_success:
        run_result = ['p', '计算表达式：{}\n结果为：{}'.format(final_expression, eval_result)]
    else:
        raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))
    return run_result, eval_success, eval_result, final_expression
