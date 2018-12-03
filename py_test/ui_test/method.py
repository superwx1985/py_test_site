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
def get_public_elements(name, public_elements):
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
def wait_for_text_present(dr, text, timeout, base_element=None, print_=True, logger=logging.getLogger('py_test')):
    dr.implicitly_wait(0.5)
    elements = list()
    start_time = time.time()
    last_print_time = 0
    while (time.time() - start_time) <= timeout:
        if isinstance(base_element, WebElement):
            find_result = vic_find_object.find_with_condition(text, base_element.text, logger=logger)
            if find_result.is_matched:
                elements_temp = base_element.find_elements_by_xpath('.//*[contains(text(),"' + text + '")]')
                for element in elements_temp:
                    if element.is_displayed():
                        elements.append(element)
            js_str = '''
            var nodeList = arguments[0].childNodes
            var text = arguments[1]
            for(var i=0; i<nodeList.length; i++){
                if (nodeList[i].nodeValue!=null && nodeList[i].nodeValue.indexOf(text)>0){
                    return true;
                }
            }
            return false;
            '''
            js_result = dr.execute_script(js_str, base_element, text)
            if js_result:
                elements.append(base_element)
        else:
            _body = dr.find_element_by_tag_name('body')
            find_result = vic_find_object.find_with_condition(text, _body.text, logger=logger)
            if find_result.is_matched:
                elements_temp = dr.find_elements_by_xpath('//body//*[contains(text(),"' + text + '")]')
                for element in elements_temp:
                    if element.is_displayed():
                        elements.append(element)
                if 0 == len(elements):  # 如果文本不在元素的第一个子节点，用text()可能会找不到
                    elements.append(_body)
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            logger.info('经过%s秒 - 找到%s个期望文本' % (elapsed_time, len(elements)))
            last_print_time = now_time
        if len(elements) > 0:
            break
    dr.implicitly_wait(timeout)
    elapsed_time = str(round(time.time() - start_time, 2))
    msg = '经过{}秒 - 找到{}个期望文本【{}】'.format(elapsed_time, len(elements), text)
    if len(elements) == 0:
        run_result = ['f', msg]
    else:
        run_result = ['p', msg]
    return run_result, elements


# 等待字符串出现，包含定位符
def wait_for_text_present_with_locator(
        dr, by, locator, text, timeout, index_, base_element=None, variable_elements=None, print_=True,
        logger=logging.getLogger('py_test')):
    dr.implicitly_wait(0.5)
    start_time = time.time()
    last_print_time = 0
    elements = list()
    fail_elements = list()
    elements_temp = list()
    while (time.time() - start_time) <= timeout:
        elements = list()
        fail_elements = list()
        run_result_temp, elements_temp, elements_all = wait_for_element_visible(
            dr, by, locator, 1, base_element, variable_elements, print_=False, logger=logger)
        if len(elements_temp) == 0:
            now_time = time.time()
            if print_ and now_time - last_print_time >= 1:
                elapsed_time = str(round(now_time - start_time, 2))
                logger.info('经过%s秒 - 未找到期望元素' % elapsed_time)
                last_print_time = now_time
                continue
        else:
            if index_ is None:
                for element_temp in elements_temp:
                    element_text = dr.execute_script(
                        'return arguments[0].textContent||arguments[0].innerText||arguments[0].value',
                        element_temp)
                    find_result = vic_find_object.find_with_condition(text, element_text, logger=logger)
                    if find_result.is_matched:
                        elements.append(element_temp)
                    else:
                        fail_elements.append(element_temp)
            elif index_ > (len(elements_temp) - 1):
                raise exceptions.ElementNotSelectableException(
                    str(len(elements_temp)) + ' elements found, the provided index (' + str(
                        index_) + ') is out of range (0 ~ ' + str(len(elements) - 1) + ')')
            else:
                element_text = dr.execute_script(
                    'return arguments[0].textContent||arguments[0].innerText||arguments[0].value',
                    elements_temp[index_])
                find_result = vic_find_object.find_with_condition(text, element_text, logger=logger)
                if find_result.is_matched:
                    elements.append(elements_temp[index_])
                else:
                    fail_elements.append(elements_temp[index_])
            now_time = time.time()
            if print_ and now_time - last_print_time >= 1:
                elapsed_time = str(round(now_time - start_time, 2))
                logger.info('经过%s秒 - 找到期望元素%r个，其中有%r个元素包含期望文本' % (elapsed_time, len(elements_temp), len(elements)))
                last_print_time = now_time
        if len(elements) > 0 and (len(elements) == len(elements_temp) or index_ is not None):
            break
    dr.implicitly_wait(timeout)
    elapsed_time = str(round(time.time() - start_time, 2))
    msg = '经过{}秒 - 找到期望元素【By:{}|Locator:{}】{}个，其中有{}个元素包含期望文本【{}】'.format(
        elapsed_time, by, locator, len(elements_temp), len(elements), text)
    if len(elements) == 0 or (len(elements) < len(elements_temp) and index_ is None):
        run_result = ['f', msg]
    else:
        run_result = ['p', msg]
    return run_result, elements, fail_elements


# 等待元素出现
def wait_for_element_present(
        dr, by, locator, timeout, base_element=None, variable_elements=None, print_=True,
        logger=logging.getLogger('py_test')):
    elements = list()
    dr.implicitly_wait(0.5)
    start_time = time.time()
    last_print_time = 0
    while (time.time() - start_time) <= timeout:
        if variable_elements is not None:
            elements = variable_elements
        else:
            if isinstance(base_element, WebElement):
                elements = base_element.find_elements(by, locator)
            else:
                elements = dr.find_elements(by, locator)
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            logger.info('经过%s秒 - 找到期望元素%r个' % (elapsed_time, len(elements)))
            last_print_time = now_time
        if len(elements) > 0:
            break
    dr.implicitly_wait(timeout)
    elapsed_time = str(round(time.time() - start_time, 2))
    msg = '经过{}秒 - 找到期望元素【By:{}|Locator:{}】{}个'.format(elapsed_time, by, locator, len(elements))
    if len(elements) == 0:
        run_result = ['f', msg]
    else:
        run_result = ['p', msg]
    return run_result, elements


# 获取元素
def get_element(
        dr, by, locator, timeout, index_, base_element=None, variable_elements=None, print_=True,
        logger=logging.getLogger('py_test')):
    if variable_elements is not None:
        elements = variable_elements
    else:
        run_result_temp, elements = wait_for_element_present(dr, by, locator, timeout, base_element=base_element,
                                                             variable_elements=None, print_=print_, logger=logger)
        if run_result_temp[0] == 'f':
            raise exceptions.NoSuchElementException('无法执行动作，因为：{}'.format(run_result_temp[1]))
    if len(elements) == 1 and index_ in (None, 0):
        element = elements[0]
    elif index_ is None:
        raise ValueError('找到%r个元素，请指定一个index' % len(elements))
    elif index_ > (len(elements) - 1):
        raise ValueError('找到%r个元素，但指定的index超出可用范围（0到%r）' % (len(elements), len(elements) - 1))
    else:
        element = elements[index_]
    return element


# 等待元素可见
def wait_for_element_visible(
        dr, by, locator, timeout, base_element=None, variable_elements=None, print_=True,
        logger=logging.getLogger('py_test')):
    elements = list()
    visible_elements = list()
    dr.implicitly_wait(0.5)
    start_time = time.time()
    last_print_time = 0
    while (time.time() - start_time) <= timeout:
        visible_elements = list()
        if variable_elements is not None:
            elements = variable_elements
        else:
            if isinstance(base_element, WebElement):
                elements = base_element.find_elements(by, locator)
            else:
                elements = dr.find_elements(by, locator)
        if len(elements) > 0:
            for element in elements:
                if element.is_displayed():
                    visible_elements.append(element)
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            logger.info('经过%s秒 - 找到期望元素%r个，其中可见元素%r个' % (elapsed_time, len(elements), len(visible_elements)))
            last_print_time = now_time
        if len(visible_elements) > 0:
            break
    dr.implicitly_wait(timeout)
    elapsed_time = str(round(time.time() - start_time, 2))
    msg = '经过{}秒 - 找到期望元素【By:{}|Locator:{}】{}个，其中可见元素{}个'.format(
        elapsed_time, by, locator, len(elements), len(visible_elements))
    if len(elements) == 0 or len(visible_elements) == 0:
        run_result = ['f', msg]
    else:
        run_result = ['p', msg]
    return run_result, visible_elements, elements


# 获取可见元素
def get_variable_element(
        dr, by, locator, timeout, index_, base_element=None, variable_elements=None, print_=True,
        logger=logging.getLogger('py_test')):
    if variable_elements is not None:
        elements = variable_elements
    else:
        run_result_temp, elements, elements_all = wait_for_element_visible(dr, by, locator, timeout, base_element,
                                                                           print_=print_, logger=logger)
        if run_result_temp[0] == 'f':
            raise exceptions.NoSuchElementException('未找到指定的元素，{}'.format(run_result_temp[1]))
    if len(elements) == 1 and index_ in (None, 0):
        element = elements[0]
    elif index_ is None:
        raise ValueError('找到%r个元素，请指定一个index' % len(elements))
    elif index_ > (len(elements) - 1):
        raise ValueError('找到%r个元素，但指定的index超出可用范围（0到%r）' % (len(elements), len(elements) - 1))
    else:
        element = elements[index_]
    return element


# 等待元素可见，包含数量限制
def wait_for_element_visible_with_data(dr, by, locator, data, timeout, base_element=None, variable_elements=None,
                                       print_=True, logger=logging.getLogger('py_test')):
    start_time = time.time()
    last_print_time = 0
    compare_result = False
    visible_elements = list()
    elements = list()
    while (time.time() - start_time) <= timeout:
        run_result_temp, visible_elements, elements = wait_for_element_visible(
            dr, by, locator, 1, base_element, variable_elements, print_=False, logger=logger)
        if len(visible_elements) == 0:
            now_time = time.time()
            if print_ and now_time - last_print_time >= 1:
                elapsed_time = str(round(now_time - start_time, 2))
                logger.info('经过%s秒 - 找到期望元素%r个，其中可见元素%r个' % (elapsed_time, len(elements), len(visible_elements)))
                last_print_time = now_time
                continue
        eo = vic_eval.EvalObject(data, {'x': len(visible_elements)}, logger)
        eval_success, eval_result, final_expression = eo.get_eval_result()
        compare_result = eval_result
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            if compare_result is True:
                msg = '经过%s秒 - 找到期望元素%r个，其中可见元素%r个，符合给定的数量限制' % (elapsed_time, len(elements), len(visible_elements))
            else:
                msg = '经过%s秒 - 找到期望元素%r个，其中可见元素%r个，不符合给定的数量限制' % (elapsed_time, len(elements), len(visible_elements))
            logger.info(msg)
            last_print_time = now_time
        if compare_result is True:
            break
    elapsed_time = str(round(time.time() - start_time, 2))
    if compare_result is True:
        msg = '经过{}秒 - 找到期望元素【By:{}|Locator:{}】{}个，其中可见元素{}个，符合给定的数量限制'.format(
            elapsed_time, by, locator, len(elements), len(visible_elements))

        run_result = ['p', msg]
    else:
        msg = '经过{}秒 - 找到期望元素【By:{}|Locator:{}】{}个，其中可见元素{}个，不符合给定的数量限制'.format(
            elapsed_time, by, locator, len(elements), len(visible_elements))
        run_result = ['f', msg]
    return run_result, visible_elements


# 等待元素消失
def wait_for_element_disappear(
        dr, by, locator, timeout, base_element=None, variable_elements=None, print_=True,
        logger=logging.getLogger('py_test')):
    visible_elements = list()
    dr.implicitly_wait(0.5)
    start_time = time.time()
    last_print_time = 0
    elements = list()
    while (time.time() - start_time) <= timeout:
        visible_elements = list()
        if variable_elements is not None:
            elements = variable_elements
        else:
            if isinstance(base_element, WebElement):
                elements = base_element.find_elements(by, locator)
            else:
                elements = dr.find_elements(by, locator)
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            logger.info('经过%s秒 - 找到期望元素%r个，其中可见元素%r个' % (elapsed_time, len(elements), len(visible_elements)))
            last_print_time = now_time
        if len(elements) == 0:
            break
        else:
            for element in elements:
                if element.is_displayed():
                    visible_elements.append(element)
            if len(visible_elements) == 0:
                break
    dr.implicitly_wait(timeout)
    elapsed_time = str(round(time.time() - start_time, 2))
    msg = '经过{}秒 - 找到期望元素【By:{}|Locator:{}】{}个，其中可见元素{}个'.format(
        by, locator, elapsed_time, len(elements), len(visible_elements))
    if len(visible_elements) != 0:
        run_result = ['f', msg]
    else:
        run_result = ['p', msg]
    return run_result, visible_elements


# 跳转到url
def go_to_url(dr, url):
    dr.get(url)
    run_result = ['p', '成功打开URL【{}】'.format(url)]
    return run_result


# 等待页面跳转
def wait_for_page_redirect(dr, new_url, timeout, print_=True, logger=logging.getLogger('py_test')):
    is_passed = False
    start_time = time.time()
    last_print_time = 0
    while (time.time() - start_time) <= timeout:
        current_url = dr.current_url
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            logger.info('经过%s秒 - 验证新URL是否符合期望' % elapsed_time)
            last_print_time = now_time
        find_result = vic_find_object.find_with_condition(new_url, current_url, logger=logger)
        if find_result.is_matched:
            is_passed = True
            break
    elapsed_time = str(round(time.time() - start_time, 2))
    if not is_passed:
        run_result = ['f', '经过{}秒 - 新URL不符合期望【{}】'.format(elapsed_time, new_url)]
    else:
        run_result = ['p', '经过{}秒 - 新URL符合期望【{}】'.format(elapsed_time, new_url)]
    return run_result, new_url


# 获取URL
def get_url(dr, condition_value, logger=logging.getLogger('py_test')):
    data = dr.current_url
    if condition_value:
        find_result = vic_find_object.find_with_condition(condition_value, data, logger=logger)
        if find_result.is_matched:
            data = ''
            if find_result.re_result:
                data = find_result.re_result[0]
            run_result = ['p', '找到符合条件【{}】的URL内容【{}】'.format(condition_value, data)]
        else:
            run_result = ['f', '找不到符合条件【{}】的URL内容'.format(condition_value)]
    else:
        run_result = ['p', '获取到URL【{}】'.format(data)]
    return run_result, data


# 尝试点击
def try_to_click(
        dr, by, locator, timeout, index_, base_element=None, variable_elements=None, print_=True,
        logger=logging.getLogger('py_test')):
    element = get_variable_element(
        dr, by, locator, timeout, index_, base_element=base_element, variable_elements=variable_elements, print_=print_,
        logger=logger)

    highlight_for_a_moment(dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    element.click()
    run_result = ['p', '点击元素【By:{}|Locator:{}】'.format(by, locator)]
    return run_result, [element]


# 尝试输入
def try_to_enter(
        dr, by, locator, data, timeout, index_, base_element=None, variable_elements=None, print_=True,
        logger=logging.getLogger('py_test')):
    element = get_variable_element(
        dr, by, locator, timeout, index_, base_element=base_element, variable_elements=variable_elements, print_=print_,
        logger=logger)

    highlight_for_a_moment(dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    element.clear()
    element.send_keys(data)
    run_result = ['p', '在元素【By:{}|Locator:{}】中输入【{}】'.format(by, locator, data)]
    return run_result, [element]


# 尝试选择
def try_to_select(
        dr, by, locator, data, timeout, index_, base_element=None, variable_elements=None, print_=True,
        logger=logging.getLogger('py_test')):
    element = get_variable_element(
        dr, by, locator, timeout, index_, base_element=base_element, variable_elements=variable_elements, print_=print_,
        logger=logger)

    highlight_for_a_moment(dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    select = Select(element)
    # 如果data为空则全不选
    if not data:
        select.deselect_all()
    # 如果data为字符串all
    elif data.upper() == 'all':
        # 如果select是多选
        if select.is_multiple:
            for i in range(len(select.options)):
                select.select_by_index(i)
        else:
            raise ValueError('单项选择框不允许全选')
    # 尝试把data转为json对象
    else:
        try:
            option_list = json.loads(data)
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
            by, locator, '|'.join(selected_text_list))]
    return run_result, [element]


# 获取特殊键组合
def get_special_keys(data_, logger=logging.getLogger('py_test')):
    data_ = data_.replace('\\+', '#{$plus}#')
    data_list = data_.split('+')
    keys = list()
    from selenium.webdriver.common.keys import Keys
    for key_str in data_list:
        key_str = key_str.replace('#{$plus}#', '+')
        if key_str.find('$') == 0 and len(key_str) > 1:
            try:
                key_str = getattr(Keys, key_str.replace('$', '', 1).upper())
            except AttributeError:
                logger.warning('【{}】不是一个合法的特殊键，不进行转换'.format(key_str))
            keys.append(key_str)
        else:
            keys.append(key_str)
    return keys


# 特殊动作
def perform_special_action(
        dr, by, locator, data, timeout, index_, special_action, base_element=None, variables=None,
        global_variables=None, variable_elements=None, print_=True, logger=logging.getLogger('py_test')):
    if by == '':
        element = None
    else:
        element = get_element(
            dr, by, locator, timeout, index_, base_element=base_element, variable_elements=variable_elements,
            print_=print_, logger=logger)

    if special_action == 'click':
        ActionChains(dr).click(element).perform()

    elif special_action == 'click_and_hold':
        ActionChains(dr).click_and_hold(element).perform()

    elif special_action == 'context_click':
        ActionChains(dr).context_click(element).perform()

    elif special_action == 'double_click':
        ActionChains(dr).double_click(element).perform()

    elif special_action == 'release':
        ActionChains(dr).release(element).perform()

    elif special_action == 'move_by_offset':
        data = data.split(',')
        if len(data) < 2:
            raise ValueError('必须指定一组偏移坐标')
        xoffset = change_string_to_digit(data[0].strip())
        yoffset = change_string_to_digit(data[1].strip())
        ActionChains(dr).move_by_offset(xoffset, yoffset).perform()

    elif special_action == 'move_to_element':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个元素')
        ActionChains(dr).move_to_element(element).perform()

    elif special_action == 'move_to_element_with_offset':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个元素')
        data = data.split(',')
        if len(data) < 2:
            raise ValueError('必须指定一组偏移坐标')
        xoffset = change_string_to_digit(data[0].strip())
        yoffset = change_string_to_digit(data[1].strip())
        ActionChains(dr).move_to_element_with_offset(element, xoffset, yoffset).perform()

    elif special_action == 'drag_and_drop':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个元素')
        target_element = vic_variables.get_elements(data, variables, global_variables)[0]
        if not isinstance(target_element, WebElement):
            raise ValueError('必须指定一个目标元素')
        ActionChains(dr).drag_and_drop(element, target_element).perform()

    elif special_action == 'drag_and_drop_by_offset':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个元素')
        data = data.split(',')
        if len(data) < 2:
            raise ValueError('必须指定一组目标坐标')
        xoffset = change_string_to_digit(data[0].strip())
        yoffset = change_string_to_digit(data[1].strip())
        ActionChains(dr).drag_and_drop_by_offset(element, xoffset, yoffset).perform()

    elif special_action == 'key_down':
        ActionChains(dr).key_down(element).perform()

    elif special_action == 'key_up':
        ActionChains(dr).key_up(element).perform()

    elif special_action == 'send_keys':
        keys = get_special_keys(data, logger=logger)
        ActionChains(dr).send_keys(keys).perform()

    elif special_action == 'send_keys_to_element':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个被操作元素')
        keys = get_special_keys(data, logger=logger)
        ActionChains(dr).send_keys_to_element(element, keys).perform()

    else:
        raise ValueError('无法处理的特殊操作[%s]' % special_action)

    run_result = ['p', '特殊动作执行完毕']
    return run_result, [element]


# 尝试滚动到元素位置
def try_to_scroll_into_view(
        dr, by, locator, timeout, index_, base_element=None, variable_elements=None, print_=True,
        logger=logging.getLogger('py_test')):
    element = get_element(
        dr, by, locator, timeout, index_, base_element=base_element, variable_elements=variable_elements, print_=print_,
        logger=logger)

    highlight_for_a_moment(dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    dr.execute_script('arguments[0].scrollIntoView()', element)
    run_result = ['p', '移动窗口到元素【By:{}|Locator:{}】的位置'.format(by, locator)]
    return run_result, [element]


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
def try_to_switch_to_window(
        dr, by, locator, data, timeout, index_, current_window_handle, base_element=None, print_=True,
        logger=logging.getLogger('py_test')):
    start_time = time.time()
    last_print_time = 0
    success_ = False
    new_window_handle = None
    if index_ is None:
        index_ = 0
    while (time.time() - start_time) <= timeout:
        for window_handle in dr.window_handles:
            if window_handle != current_window_handle:
                dr.switch_to.window(window_handle)
                # 如果定位信息不全，但提供了data，则把data视为窗口标题
                if (by == '' or locator == '') and data != '':
                    by = 'xpath'
                    locator = '/html/head/title[contains(text(), "{}")]'.format(data)
                if by != '' and locator != '':
                    run_result_temp, elements = wait_for_element_present(
                        dr, by, locator, 1, base_element=base_element, variable_elements=None, print_=False,
                        logger=logger)
                    if index_ > (len(elements) - 1):
                        continue
                    else:
                        new_window_handle = window_handle
                        success_ = True
                        break
                else:
                    new_window_handle = window_handle
                    success_ = True
                    break
        now_time = time.time()
        if success_:
            break
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            logger.info('经过%s秒 - 尝试切换到新窗口' % elapsed_time)
            last_print_time = now_time
    elapsed_time = str(round(time.time() - start_time, 2))
    if not success_:
        raise exceptions.NoSuchWindowException('经过%s秒 - 无法切换到新窗口' % elapsed_time)
    else:
        try:
            title = dr.find_element_by_tag_name('title')
            title_str = title.text
        except exceptions.WebDriverException:
            title_str = '（无标题）'
        run_result = ['p', '经过{}秒 - 切换到新窗口【{}】'.format(elapsed_time, title_str)]
    return run_result, new_window_handle


# 尝试切换frame
def try_to_switch_to_frame(
        dr, by, locator, index_, timeout, base_element=None, print_=True,
        logger=logging.getLogger('py_test')):
    if index_ is None:
        index_ = 0
    start_time = time.time()
    last_print_time = 0
    success_ = False
    while (time.time() - start_time) <= timeout:
        if by != '' and locator != '':
            run_result_temp, elements = wait_for_element_present(
                dr, by, locator, 1, base_element=base_element, variable_elements=None, print_=False, logger=logger)
            if run_result_temp[0] == 'p':
                frame = elements[index_]
                dr.switch_to.frame(frame)
                success_ = True
                break
        else:
            try:
                dr.switch_to.frame(index_)
                success_ = True
                break
            except exceptions.NoSuchFrameException:
                pass
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            logger.info('经过%s秒 - 尝试切换到frame' % elapsed_time)
            last_print_time = now_time
    elapsed_time = str(round(time.time() - start_time, 2))
    if not success_:
        raise exceptions.NoSuchFrameException('经过%s秒 - 无法切换到frame' % elapsed_time)
    else:
        run_result = ['p', '经过{}秒 - 切换到frame【By:{}|Locator:{}】'.format(elapsed_time, by, locator)]
    return run_result


# 运行javascript
def run_js(
        dr, by, locator, data, timeout, index_, base_element=None, variable_elements=None, print_=True,
        logger=logging.getLogger('py_test')):
    if by in (None, ''):
        js_result = dr.execute_script(data)
    else:
        if variable_elements is not None:
            elements = variable_elements
        else:
            run_result_temp, elements = wait_for_element_present(
                dr, by, locator, timeout, base_element=base_element, variable_elements=None, print_=print_,
                logger=logger)
            if run_result_temp[0] == 'f':
                raise exceptions.NoSuchElementException(run_result_temp[1])
        if index_ is None:
            js_result = dr.execute_script(data, elements)
        elif index_ > (len(elements) - 1):
            raise ValueError('找到%r个元素，但指定的index超出可用范围（0到%r）' % (len(elements), len(elements) - 1))
        else:
            js_result = dr.execute_script(data, elements[index_])
    if isinstance(js_result, WebElement):
        js_result = [js_result]
    msg = 'JavaScript执行完毕，返回值为：\n%s' % js_result
    if print_:
        logger.info(msg)
    run_result = ['p', msg]
    return run_result, js_result


# 获取元素文本
def get_element_text(
        dr, by, locator, timeout, index_, base_element=None, variable_elements=None, print_=True,
        logger=logging.getLogger('py_test')):
    element = get_element(
        dr, by, locator, timeout, index_, base_element=base_element, variable_elements=variable_elements, print_=print_,
        logger=logger)

    highlight_for_a_moment(dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    text = element.text
    run_result = ['p', '元素【By:{}|Locator:{}】的文本为：{}'.format(by, locator, text)]
    return run_result, text


# 获取元素属性
def get_element_attr(
        dr, by, locator, data, timeout, index_, base_element=None, variable_elements=None, print_=True,
        logger=logging.getLogger('py_test')):
    element = get_element(
        dr, by, locator, timeout, index_, base_element=base_element, variable_elements=variable_elements, print_=print_,
        logger=logger)

    highlight_for_a_moment(dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    attr = element.get_attribute(data)
    if attr:
        run_result = ['p', '元素【By:{}|Locator:{}】的【{}】属性的值为：{}'.format(by, locator, data, attr)]
    else:
        run_result = ['f', '元素【By:{}|Locator:{}】不存在【{}】属性'.format(by, locator, data)]
    return run_result, attr
