# ===========================================================================
# ID = "id"
# XPATH = "xpath"
# LINK_TEXT = "link text"
# PARTIAL_LINK_TEXT = "partial link text"
# NAME = "name"
# TAG_NAME = "tag name"
# CLASS_NAME = "class name"
# CSS_SELECTOR = "css selector"
# ===========================================================================

import time
import uuid
import os
import io
import datetime
from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
from py_test.vic_tools import vic_find_object, vic_eval
from py_test.vic_tools.vic_str_handle import change_string_to_digit
from py_test.general import vic_log


# 获取浏览器driver
def get_driver(config):
    if config.ui_selenium_client == 1:  # 本地
        if config.ui_driver_type == 1:  # Chrome
            chrome_option = webdriver.ChromeOptions()
            chrome_option._arguments = ['test-type', "start-maximized", "no-default-browser-check"]
            dr = webdriver.Chrome(chrome_options=chrome_option)
        elif config.ui_driver_type == 2:  # IE
            dr = webdriver.Ie()
        elif config.ui_driver_type == 3:  # FireFox
            if config.ui_driver_ff_profile:
                dr = webdriver.Firefox(firefox_profile=webdriver.FirefoxProfile(config.ui_driver_ff_profile))
            else:
                dr = webdriver.Firefox()
        elif config.ui_driver_type == 4:  # PhantomJS
            dr = webdriver.PhantomJS()
        else:
            raise ValueError('浏览器类型错误，请检查配置项')
    elif config.ui_selenium_client == 2:  # 远程
        if not config.ui_remote_ip or not config.ui_remote_port:
            raise ValueError('缺少远程驱动配置参数，检查配置项')
        if config.ui_driver_type == 1:  # Chrome
            dr = webdriver.Remote(
                command_executor='http://{}:{}/wd/hub'.format(config.ui_remote_ip, config.ui_remote_port),
                desired_capabilities=DesiredCapabilities.CHROME
            )
        elif config.ui_driver_type == 2:  # IE
            dr = webdriver.Remote(
                command_executor='http://{}:{}/wd/hub'.format(config.ui_remote_ip, config.ui_remote_port),
                desired_capabilities=DesiredCapabilities.INTERNETEXPLORER
            )
        elif config.ui_driver_type == 3:  # FireFox
            dr = webdriver.Remote(
                command_executor='http://{}:{}/wd/hub'.format(config.ui_remote_ip, config.ui_remote_port),
                desired_capabilities=DesiredCapabilities.FIREFOX
            )
        elif config.ui_driver_type == 4:  # PhantomJS
            dr = webdriver.Remote(
                command_executor='http://{}:{}/wd/hub'.format(config.ui_remote_ip, config.ui_remote_port),
                desired_capabilities=DesiredCapabilities.PHANTOMJS
            )
        else:
            raise ValueError('浏览器类型错误，请检查配置项')
    else:
        raise ValueError('驱动类型错误，请检查配置项')

    if config.ui_window_size == 2:
        if not config.ui_window_width or not config.ui_window_height:
            raise ValueError('自定义窗口但未指定大小，请检查配置项')
        dr.set_window_size(config.ui_window_width, config.ui_window_height)
        dr.set_window_position(0, 0)
    else:
        dr.maximize_window()
    return dr


# 获取公共元素
def get_public_elements(name, public_elements):
    try:
        element_info = public_elements.get_element_info(name)
    except KeyError:
        raise ValueError('找不到公共元素【{}】'.format(name))
    element_by = element_info.by
    element_locator = element_info.locator
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
        from selenium.common.exceptions import StaleElementReferenceException
        try:
            dr.execute_script(
                '''var element = arguments[0];
                var original_style = arguments[1];
                element.setAttribute("style", original_style + ";");''',
                element, original_style)
        except StaleElementReferenceException:
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
def wait_for_text_present(dr, text, timeout, base_element, print_=True):
    logger = vic_log.get_thread_logger()
    dr.implicitly_wait(0.5)
    elements = list()
    start_time = time.time()
    last_print_time = 0
    while (time.time() - start_time) <= timeout:
        if isinstance(base_element, WebElement):
            find_result = vic_find_object.find_with_condition(text, base_element.text)
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
            find_result = vic_find_object.find_with_condition(text, _body.text)
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
            logger.debug('经过%s秒 - 找到%s个期望文本' % (elapsed_time, len(elements)))
            last_print_time = now_time
        if len(elements) > 0:
            break
    dr.implicitly_wait(timeout)
    elapsed_time = str(round(time.time() - start_time, 2))
    msg = '经过%s秒 - 找到%s个期望文本' % (elapsed_time, len(elements))
    if len(elements) == 0:
        run_result = ('f', msg)
    else:
        run_result = ('p', msg)
    return run_result, elements


# 等待字符串出现，包含定位符
def wait_for_text_present_with_locator(dr, by, locator, text, timeout, index_, base_element, variable_elements=None,
                                       print_=True):
    logger = vic_log.get_thread_logger()
    dr.implicitly_wait(0.5)
    start_time = time.time()
    last_print_time = 0
    elements = list()
    fail_elements = list()
    elements_temp = list()
    while (time.time() - start_time) <= timeout:
        elements = list()
        fail_elements = list()
        run_result_temp, elements_temp, elements_all = wait_for_element_visible(dr, by, locator, 1, base_element,
                                                                                variable_elements)
        if len(elements_temp) == 0:
            now_time = time.time()
            if print_ and now_time - last_print_time >= 1:
                elapsed_time = str(round(now_time - start_time, 2))
                logger.debug('经过%s秒 - 未找到期望元素' % elapsed_time)
                last_print_time = now_time
                continue
        else:
            if index_ is None:
                for element_temp in elements_temp:
                    element_text = dr.execute_script('return arguments[0].textContent||arguments[0].innerText',
                                                     element_temp)
                    find_result = vic_find_object.find_with_condition(text, element_text)
                    if find_result.is_matched:
                        elements.append(element_temp)
                    else:
                        fail_elements.append(element_temp)
            elif index_ > (len(elements_temp) - 1):
                raise exceptions.ElementNotSelectableException(
                    str(len(elements_temp)) + ' elements found, the provided index (' + str(
                        index_) + ') is out of range (0 ~ ' + str(len(elements) - 1) + ')')
            else:
                element_text = dr.execute_script('return arguments[0].textContent||arguments[0].innerText',
                                                 elements_temp[index_])
                find_result = vic_find_object.find_with_condition(text, element_text)
                if find_result.is_matched:
                    elements.append(elements_temp[index_])
                else:
                    fail_elements.append(elements_temp[index_])
            now_time = time.time()
            if print_ and now_time - last_print_time >= 1:
                elapsed_time = str(round(now_time - start_time, 2))
                logger.debug('经过%s秒 - 找到期望元素%r个，其中有%r个元素包含期望文本' % (elapsed_time, len(elements_temp), len(elements)))
                last_print_time = now_time
        if len(elements) > 0 and (len(elements) == len(elements_temp) or index_ is not None):
            break
    dr.implicitly_wait(timeout)
    elapsed_time = str(round(time.time() - start_time, 2))
    msg = '经过%s秒 - 找到期望元素%r个，其中有%r个元素包含期望文本' % (elapsed_time, len(elements_temp), len(elements))
    if len(elements) == 0 or len(elements) < len(elements_temp):
        run_result = ('f', msg)
    else:
        run_result = ('p', msg)
    return run_result, elements, fail_elements


# 等待元素出现
def wait_for_element_present(dr, by, locator, timeout, base_element, variable_elements=None, print_=True):
    logger = vic_log.get_thread_logger()
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
            logger.debug('经过%s秒 - 找到期望元素%r个' % (elapsed_time, len(elements)))
            last_print_time = now_time
        if len(elements) > 0:
            break
    dr.implicitly_wait(timeout)
    elapsed_time = str(round(time.time() - start_time, 2))
    msg = '经过%s秒 - 找到期望元素%r个' % (elapsed_time, len(elements))
    if len(elements) == 0:
        run_result = ('f', msg)
    else:
        run_result = ('p', msg)
    return run_result, elements


# 等待元素可见
def wait_for_element_visible(dr, by, locator, timeout, base_element, variable_elements=None, print_=True):
    logger = vic_log.get_thread_logger()
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
            logger.debug('经过%s秒 - 找到期望元素%r个，其中可见元素%r个' % (elapsed_time, len(elements), len(visible_elements)))
            last_print_time = now_time
        if len(visible_elements) > 0:
            break
    dr.implicitly_wait(timeout)
    elapsed_time = str(round(time.time() - start_time, 2))
    msg = '经过%s秒 - 找到期望元素%r个，其中可见元素%r个' % (elapsed_time, len(elements), len(visible_elements))
    if len(elements) == 0 or len(visible_elements) == 0:
        run_result = ('f', msg)
    else:
        run_result = ('p', msg)
    return run_result, visible_elements, elements


# 等待元素可见，包含数量限制
def wait_for_element_visible_with_data(dr, by, locator, data, timeout, base_element, variable_elements=None,
                                       print_=True):
    logger = vic_log.get_thread_logger()
    start_time = time.time()
    last_print_time = 0
    compare_result = False
    visible_elements = list()
    elements = list()
    while (time.time() - start_time) <= timeout:
        run_result_temp, visible_elements, elements = wait_for_element_visible(dr, by, locator, 1, base_element,
                                                                               variable_elements, print_=False)
        if len(visible_elements) == 0:
            now_time = time.time()
            if print_ and now_time - last_print_time >= 1:
                elapsed_time = str(round(now_time - start_time, 2))
                logger.debug('经过%s秒 - 找到期望元素%r个，其中可见元素%r个' % (elapsed_time, len(elements), len(visible_elements)))
                last_print_time = now_time
                continue
        eo = vic_eval.EvalObject(data, {'x': len(visible_elements)})
        eval_success, eval_result, final_expression = eo.get_eval_result()
        compare_result = eval_result
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            if compare_result is True:
                msg = '经过%s秒 - 找到期望元素%r个，其中可见元素%r个，符合给定的数量限制' % (elapsed_time, len(elements), len(visible_elements))
            else:
                msg = '经过%s秒 - 找到期望元素%r个，其中可见元素%r个，不符合给定的数量限制' % (elapsed_time, len(elements), len(visible_elements))
            logger.debug(msg)
            last_print_time = now_time
        if compare_result is True:
            break
    elapsed_time = str(round(time.time() - start_time, 2))
    if compare_result is True:
        msg = '经过%s秒 - 找到期望元素%r个，其中可见元素%r个，符合给定的数量限制' % (elapsed_time, len(elements), len(visible_elements))
        run_result = ('p', msg)
    else:
        msg = '经过%s秒 - 找到期望元素%r个，其中可见元素%r个，不符合给定的数量限制' % (elapsed_time, len(elements), len(visible_elements))
        run_result = ('f', msg)
    return run_result, visible_elements


# 等待元素消失
def wait_for_element_disappear(dr, by, locator, timeout, base_element, variable_elements=None, print_=True):
    logger = vic_log.get_thread_logger()
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
            logger.debug('经过%s秒 - 找到期望元素%r个，其中可见元素%r个' % (elapsed_time, len(elements), len(visible_elements)))
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
    msg = '经过%s秒 - 找到期望元素%r个，其中可见元素%r个' % (elapsed_time, len(elements), len(visible_elements))
    if len(visible_elements) != 0:
        run_result = ('f', msg)
    else:
        run_result = ('p', msg)
    return run_result, visible_elements


# 跳转到url
def go_to_url(dr, url):
    dr.get(url)
    run_result = ('p', '成功打开URL')
    return run_result


# 等待页面跳转
def wait_for_page_redirect(dr, new_url, timeout, print_=True):
    logger = vic_log.get_thread_logger()
    is_passed = False
    start_time = time.time()
    last_print_time = 0
    while (time.time() - start_time) <= timeout:
        current_url = dr.current_url
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            logger.debug('新URL：%s' % new_url)
            logger.debug('原URL：%s' % current_url)
            logger.debug('经过%s秒 - 验证新URL是否符合期望' % elapsed_time)
            last_print_time = now_time
        find_result = vic_find_object.find_with_condition(new_url, current_url)
        if find_result.is_matched:
            is_passed = True
            break
    elapsed_time = str(round(time.time() - start_time, 2))
    if not is_passed:
        run_result = ('f', '经过%s秒 - 新URL不符合期望' % elapsed_time)
    else:
        run_result = ('p', '经过%s秒 - 新URL符合期望' % elapsed_time)
    return run_result, new_url


# 尝试点击
def try_to_click(dr, by, locator, timeout, index_, base_element, variable_elements=None, print_=True):
    if variable_elements is not None:
        elements = variable_elements
    else:
        run_result_temp, elements, elements_all = wait_for_element_visible(dr, by, locator, timeout, base_element,
                                                                           print_=print_)
        if run_result_temp[0] == 'f':
            raise exceptions.NoSuchElementException(run_result_temp[1])
    if len(elements) == 1 and index_ in (None, 0):
        element = elements[0]
    elif index_ is None:
        raise ValueError('找到%r个元素，请指定一个index' % len(elements))
    elif index_ > (len(elements) - 1):
        raise ValueError('找到%r个元素，但指定的index超出可用范围（0到%r）' % (len(elements), len(elements) - 1))
    else:
        element = elements[index_]

    highlight_for_a_moment(dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    ActionChains(dr).click(element).perform()
    run_result = ('p', '点击成功')
    return run_result, elements


# 尝试双击
def try_to_double_click(dr, by, locator, timeout, index_, base_element, variable_elements=None, print_=True):
    if variable_elements is not None:
        elements = variable_elements
    else:
        run_result_temp, elements, elements_all = wait_for_element_visible(dr, by, locator, timeout, base_element,
                                                                           print_=print_)
        if run_result_temp[0] == 'f':
            raise exceptions.NoSuchElementException(run_result_temp[1])
    if len(elements) == 1 and index_ in (None, 0):
        element = elements[0]
    elif index_ is None:
        raise ValueError('找到%r个元素，请指定一个index' % len(elements))
    elif index_ > (len(elements) - 1):
        raise ValueError('找到%r个元素，但指定的index超出可用范围（0到%r）' % (len(elements), len(elements) - 1))
    else:
        element = elements[index_]

    highlight_for_a_moment(dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    ActionChains(dr).double_click(element).perform()
    run_result = ('p', '双击成功')
    return run_result, elements


# 尝试输入
def try_to_enter(dr, by, locator, data, timeout, index_, base_element, variable_elements=None, print_=True):
    if variable_elements is not None:
        elements = variable_elements
    else:
        run_result_temp, elements, elements_all = wait_for_element_visible(dr, by, locator, timeout, base_element,
                                                                           print_=print_)
        if run_result_temp[0] == 'f':
            raise exceptions.NoSuchElementException(run_result_temp[1])
    if len(elements) == 1 and index_ in (None, 0):
        element = elements[0]
    elif index_ is None:
        raise ValueError('找到%r个元素，请指定一个index' % len(elements))
    elif index_ > (len(elements) - 1):
        raise ValueError('找到%r个元素，但指定的index超出可用范围（0到%r）' % (len(elements), len(elements) - 1))
    else:
        element = elements[index_]

    highlight_for_a_moment(dr, (element,), 'outline: 2px dotted yellow; border: 1px solid yellow;')
    element.clear()
    element.send_keys(data)
    run_result = ('p', '输入成功')
    return run_result, elements


# 获取特殊键组合
def get_special_keys(data_):
    logger = vic_log.get_thread_logger()
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
def perform_special_action(dr, by, locator, data, timeout, index_, base_element, special_action, variables,
                           variable_elements=None, print_=True):
    if by == '':
        elements = list()
        element = None
    else:
        if variable_elements is not None:
            elements = variable_elements
        else:
            run_result_temp, elements = wait_for_element_present(dr, by, locator, timeout, base_element=base_element,
                                                                 variable_elements=None, print_=print_)
            if run_result_temp[0] == 'f':
                raise exceptions.NoSuchElementException(run_result_temp[1])
        if len(elements) == 1 and index_ in (None, 0):
            element = elements[0]
        elif index_ is None:
            raise ValueError('找到%r个元素，请指定一个index' % len(elements))
        elif index_ > (len(elements) - 1):
            raise ValueError('找到%r个元素，但指定的index超出可用范围（0到%r）' % (len(elements), len(elements) - 1))
        else:
            element = elements[index_]

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
        target_element = variables.get_elements(data)[0]
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
        keys = get_special_keys(data)
        ActionChains(dr).send_keys(keys).perform()

    elif special_action == 'send_keys_to_element':
        if not isinstance(element, WebElement):
            raise ValueError('必须指定一个被操作元素')
        keys = get_special_keys(data)
        ActionChains(dr).send_keys_to_element(element, keys).perform()

    else:
        raise ValueError('无法处理的特殊操作[%s]' % special_action)

    run_result = ('p', '操作成功')
    return run_result, elements


# 处理浏览器弹窗
def confirm_alert(dr, alert_handle, timeout, print_=True):
    logger = vic_log.get_thread_logger()
    start_time = time.time()
    last_print_time = 0
    done = False
    alert_handle_text = ''
    alert_text = ''
    from selenium.common.exceptions import NoAlertPresentException
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
        except NoAlertPresentException:
            pass
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            logger.debug('经过%s秒 - 尝试以【%s】方式关闭弹窗' % (elapsed_time, alert_handle))
            last_print_time = now_time
    elapsed_time = str(round(time.time() - start_time, 2))
    if not done:
        raise NoAlertPresentException('经过%s秒 - 找不到任何弹窗' % elapsed_time)
    return alert_handle_text, alert_text


# 尝试切换window或tap
def try_to_switch_to_window(dr, by, locator, data, timeout, index_, base_element, print_=True):
    logger = vic_log.get_thread_logger()
    current_window_handle = dr.current_window_handle
    start_time = time.time()
    last_print_time = 0
    success_ = False
    new_window_handle = None
    if index_ is None:
        index_ = 0
    from selenium.common.exceptions import NoSuchWindowException
    while (time.time() - start_time) <= timeout:
        for window_handle in dr.window_handles:
            if window_handle != current_window_handle:
                dr.switch_to.window(window_handle)
                # 如果定位信息不全，但提供了data，则把data视为窗口标题
                if (by == '' or locator == '') and data != '':
                    by = 'xpath'
                    locator = './/title[contains(text(), "{}")]'.format(data)
                if by != '' and locator != '':
                    run_result_temp, elements = wait_for_element_present(dr, by, locator, 1, base_element=base_element,
                                                                         variable_elements=None, print_=False)
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
            logger.debug('经过%s秒 - 尝试切换到新窗口' % elapsed_time)
            last_print_time = now_time
    elapsed_time = str(round(time.time() - start_time, 2))
    if not success_:
        raise NoSuchWindowException('经过%s秒 - 无法切换到新窗口' % elapsed_time)
    else:
        run_result = ('p', '经过%s秒 - 切换到新窗口【%s】' % (elapsed_time, elapsed_time))
    return run_result, new_window_handle


# 尝试切换frame
def try_to_switch_to_frame(dr, by, locator, index_, timeout, base_element, print_=True):
    logger = vic_log.get_thread_logger()
    if index_ is None:
        index_ = 0
    start_time = time.time()
    last_print_time = 0
    success_ = False
    from selenium.common.exceptions import NoSuchFrameException
    while (time.time() - start_time) <= timeout:
        if by != '' and locator != '':
            run_result_temp, elements = wait_for_element_present(dr, by, locator, 1, base_element=base_element,
                                                                 variable_elements=None, print_=False)
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
            except NoSuchFrameException:
                pass
        now_time = time.time()
        if print_ and now_time - last_print_time >= 1:
            elapsed_time = str(round(now_time - start_time, 2))
            logger.debug('经过%s秒 - 尝试切换到frame' % elapsed_time)
            last_print_time = now_time
    elapsed_time = str(round(time.time() - start_time, 2))
    if not success_:
        raise NoSuchFrameException('经过%s秒 - 无法切换到frame' % elapsed_time)
    else:
        run_result = ('p', '经过%s秒 - 切换到frame' % elapsed_time)
    return run_result


# 运行javascript
def run_js(dr, by, locator, data, timeout, index_, base_element, variable_elements=None, print_=True):
    logger = vic_log.get_thread_logger()
    if by in (None, ''):
        js_result = dr.execute_script(data)
    else:
        if variable_elements is not None:
            elements = variable_elements
        else:
            run_result_temp, elements = wait_for_element_present(dr, by, locator, timeout, base_element=base_element,
                                                                 variable_elements=None, print_=print_)
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
        logger.debug(msg)
    run_result = ('p', msg)
    return run_result, js_result


# 根据浏览器类型调取不同的截图方法
def get_screenshot(dr, element=None):
    from django.core.files.uploadedfile import UploadedFile
    from main.models import Image
    bio = io.BytesIO()
    if element:
        img = get_image_on_element(dr, element)
    else:
        if 'chrome' == dr.name:
            img = get_long_screenshot_img_for_chrome(dr)
        else:
            img = Image.open(io.BytesIO(dr.get_screenshot_as_png()))

    img.save(bio, format='png')

    name = datetime.datetime.now().strftime('%Y%m%d_%H%M%S.png')
    image = Image(name=name, img=UploadedFile(bio, name=name))
    image.save()
    bio.close()
    run_result = ('p', '截图成功')
    return run_result, image


# chrome截长图
def get_long_screenshot_img_for_chrome(dr, scroll_step=100, scroll_delay=0.1, start_height=0, max_height=10000):
    if start_height >= max_height:
        raise ValueError("截图开始高度大于最大高度")
    window_top = dr.execute_script('return scrollY;')
    if start_height != window_top:
        scroll_to_height(dr, start_height, scroll_step, scroll_delay)  # 滚动到开始高度
    window_height = dr.execute_script('return window.innerHeight;')  # 窗口高度
    time.sleep(scroll_delay)
    body_height = dr.execute_script('return document.body.scrollHeight;')  # 网页高度
    img_height = body_height - start_height  # 需要截取的高度
    if window_height <= 0 or img_height <= 0:
        raise ValueError("截图高度小于0")
    if max_height < window_height:
        max_height = window_height
    if img_height > max_height:
        img_height = max_height
    count = int((img_height / window_height))
    img1 = Image.open(io.BytesIO(dr.get_screenshot_as_png()))
    for i in range(1, count):
        scroll_to_height(dr, start_height + window_height * i, scroll_step, scroll_delay)
        img2 = Image.open(io.BytesIO(dr.get_screenshot_as_png()))
        img1 = vertical_join_image(img1, img2)
        del img2
    window_top = dr.execute_script('return scrollY;')  # 获取当前窗口位置
    if window_top < body_height - window_height:
        window_top_old = window_top
        scroll_to_height(dr, body_height - window_height, scroll_step, scroll_delay)
        window_top = dr.execute_script('return scrollY;')
        img2 = Image.open(io.BytesIO(dr.get_screenshot_as_png()))
        window_top_delta = window_top - window_top_old
        left = 0
        top = img2.size[1] - window_top_delta
        right = img2.size[0]
        bottom = img2.size[1]
        img2 = img2.crop((left, top, right, bottom))  # defines crop points
        img1 = vertical_join_image(img1, img2)
        del img2
    return img1


# 垂直合并图片
def vertical_join_image(img1, img2):
    width1 = img1.size[0]
    height1 = img1.size[1]
    width2 = img2.size[0]
    height2 = img2.size[1]
    if width1 >= width2:
        width3 = width1
    else:
        width3 = width2
    img3 = Image.new('RGB', (width3, height1 + height2))
    img3.paste(img1, (0, 0, width1, height1))
    img3.paste(img2, (0, height1, width2, height1 + height2))
    return img3


# 只截取某个元素
def get_image_on_element(dr, element):
    window_top = dr.execute_script('return scrollY;')
    dr.execute_script("arguments[0].scrollIntoView();", element)
    time.sleep(1)
    window_top_new = dr.execute_script('return scrollY;')
    scroll_height = window_top_new - window_top
    left = element.location['x']
    right = left + element.size['width']
    top = element.location['y'] - scroll_height
    bottom = top + element.size['height']

    if 'chrome' == dr.name:
        img = get_long_screenshot_img_for_chrome(dr, 100, 0.1, scroll_height, scroll_height + element.size['height'])
    else:
        img = Image.open(io.BytesIO(dr.get_screenshot_as_png()))
    # 裁剪图片
    img.crop((left, top, right, bottom))
    return img


# 下拉加载更多内容
def scroll_down_for_loading(driver, wait_time=30, print_=True):
    logger = vic_log.get_thread_logger()
    # driver.execute_script("arguments[0].scrollIntoView();")
    driver.execute_script("""
        (function () {
            var y = scrollY;
            var step = 100;
            window.scroll(0, 0);

            function f() {
                if (y < document.body.scrollHeight) {
                    y += step;
                    window.scroll(0, y);
                    setTimeout(f, 100);
                } else {
                    window.scroll(0,0);
                    document.title += "scroll-done";
                }
            }

            setTimeout(f, 1000);
        })();
    """)

    start_time = time.time()
    for i in range(wait_time):
        if "scroll-done" in driver.title:
            return
        time.sleep(1)
        if print_:
            logger.debug('经过%s秒 - 向下拖动第%s次' % (str(round(time.time() - start_time, 2)), i))


# 滚动到顶部
def scroll_to_height(dr, _to, _step, delay):
    _from = dr.execute_script('return scrollY')
    count = int((_to - _from) / _step)
    if count >= 0:
        for i in range(1, count + 1):
            dr.execute_script('window.scroll(0, arguments[0]);', _from + _step * i)
            time.sleep(delay)
    else:
        count = abs(count)
        for i in range(1, count + 1):
            dr.execute_script('window.scroll(0, arguments[0]);', _from - _step * i)
            time.sleep(delay)
    top = dr.execute_script('return scrollY')
    if top != _to:
        dr.execute_script('window.scroll(0, arguments[0]);', _to)
        time.sleep(delay)
    return count


# 生成截图路径
def get_screenshot_full_name(file_name, base_path=os.getcwd()):
    logger = vic_log.get_thread_logger()
    _name_list = os.path.splitext(file_name)
    from py_test.general.vic_method import check_name
    _name_result = check_name(_name_list[0])
    if _name_result[0]:
        file_name = _name_list[0] + '.png'
    else:
        logger.warning(_name_result[1])
        file_name = 'screenshot_{}.png'.format(uuid.uuid1())
        # file_name = 'screenshot_' + datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f") + '.png'
    return os.path.join(base_path, file_name)
