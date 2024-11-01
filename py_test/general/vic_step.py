import datetime
import time
import json
import traceback
import socket
import math
from socket import timeout as socket_timeout_error

import requests
from django.forms.models import model_to_dict
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from py_test.general import vic_variables, vic_method
from py_test.vic_tools import vic_find_object
from py_test import web_ui_test
from py_test.api_test import method as api_method
from py_test.db_test import method as db_method
from py_test.vic_tools import vic_eval, vic_date_handle
from main.models import StepResult, Step, error_handle_dict
from py_test_site.settings import LOOP_ITERATIONS_LIMIT, ERROR_PAUSE_TIMEOUT


class VicStep:
    def __init__(self, step, vic_case, step_order):
        self.logger = vic_case.logger

        self.step = step
        self.vic_case = vic_case

        self.user = vic_case.user
        self.execute_uuid = vic_case.execute_uuid

        self.id = step.pk
        self.name = step.name
        self.action_type_code = step.action.type.code
        self.action_code = step.action.code

        self.browser_alert = False
        self.browser_alert_text = ''

        # timeout为0时也要取
        self.timeout = step.timeout if step.timeout is not None else vic_case.timeout
        # ui_step_interval为0时也要取
        self.ui_step_interval = step.ui_step_interval if step.ui_step_interval is not None \
            else vic_case.ui_step_interval

        error_handle = error_handle_dict.get(step.error_handle)
        self.error_handle = error_handle if error_handle else vic_case.error_handle

        self.save_as = step.save_as

        self.ui_get_ss = vic_case.vic_suite.ui_get_ss
        self.variables = vic_case.variables
        self.global_variables = vic_case.global_variables
        self.public_elements = vic_case.public_elements
        self.config = vic_case.config

        self.step_order = step_order
        self.execute_str = '{}-{}'.format(vic_case.execute_str, step_order)
        self.loop_id = ''
        self.img_list = list()  # 截图列表
        self.status = 0
        self.force_stop_signal = False  # 强制停止信号
        self.drs = None # driver容器
        self.socket_no_response = False  # 驱动停止响应标志
        self.variable_elements = None
        self.run_result = ['p', '执行成功']
        self.elements = list()
        self.fail_elements = list()

        # 初始化result数据库对象
        self.step_result = StepResult(
            name=step.name,
            description=step.description,
            keyword=step.keyword,
            action=step.action.full_name,

            case_result=vic_case.case_result,
            step=step,
            step_order=step_order,
            creator=vic_case.user,

            result_message='',
            result_error='',
            ui_last_url='',

            snapshot=json.dumps(model_to_dict(step)) if step else None,
        )

        try:
            self.ui_by = Step.ui_by_dict.get(step.ui_by, '')
            self.ui_locator = step.ui_locator
            self.ui_index = step.ui_index
            self.ui_base_element = step.ui_base_element
            self.ui_data = step.ui_data
            self.ui_special_action = Step.ui_special_action_dict.get(step.ui_special_action, '')
            self.ui_alert_handle = Step.ui_alert_handle_dict.get(step.ui_alert_handle, 'accept')
            self.ui_alert_handle_text = step.ui_alert_handle_text

            self.api_url = step.api_url
            self.api_method = Step.api_method_dict.get(step.api_method, '')
            self.api_headers = step.api_headers
            self.api_body = step.api_body
            self.api_decode = step.api_decode
            self.api_response_status = step.api_response_status
            self.api_data = step.api_data
            self.api_save = step.api_save

            self.other_data = step.other_data
            self.other_sub_case = step.other_sub_case

            self.db_type = Step.db_type_dict.get(step.db_type, '')
            self.db_host = step.db_host
            self.db_port = step.db_port
            self.db_name = step.db_name
            self.db_user = step.db_user
            self.db_password = step.db_password
            self.db_lang = step.db_lang
            self.db_sql = step.db_sql
            self.db_data = step.db_data
        except Exception as e:
            self.logger.info('【{}】\t步骤读取出错'.format(self.execute_str), exc_info=True)
            self.step_result.result_state = 3
            self.step_result.result_message = '步骤读取出错：{}'.format(getattr(e, 'msg', str(e)))
            self.step_result.result_error = traceback.format_exc()
            raise

    # 强制停止标志
    @property
    def force_stop(self):
        if self.force_stop_signal or self.vic_case.force_stop:
            self.force_stop_signal = True
            self.status = 3
            return True
        else:
            return False

    # 暂停标志
    @property
    def pause(self):
        pause_state = False
        if self.vic_case.continue_signal:
            self.continue_()
        elif not self.force_stop and self.vic_case.pause:
            self.status = 2
            pause_state = True

        return pause_state

    def continue_(self):
        self.vic_case.continue_()
        if not self.force_stop:
            self.status = 1

    # 判断是否需要暂停
    def pause_(self, seconds=0.0, msg_format='【{}】\t已暂停{}秒，剩余{}秒'):
        if self.pause:
            if seconds <= 0:
                seconds = ERROR_PAUSE_TIMEOUT
            _timeout = math.modf(float(seconds))
            start_time = time.time()
            time.sleep(_timeout[0])  # 补上小数部分
            x = int(_timeout[1])
            for i in range(x):
                if not self.pause or self.force_stop:
                    break
                time.sleep(1)
                y = i + 1
                self.logger.info(msg_format.format(self.execute_str, y, x - y))
            self.continue_()
            return time.time() - start_time
        else:
            return 0

    # 更新测试数据
    def update_test_data(self, *args):
        var = self.variables
        gvar = self.global_variables
        logger = self.logger
        for arg in args:
            attr = getattr(self, arg)
            if arg == 'ui_base_element':
                if isinstance(attr, str):
                    _attr = str(vic_method.replace_special_value(attr, var, gvar, logger))
                    setattr(self, arg, vic_variables.get_elements(_attr, var, gvar)[0] if _attr else None)
            else:
                setattr(self, arg, str(vic_method.replace_special_value(attr, var, gvar, logger)))

        if 'ui_locator' in args:
            if self.ui_by == 'variable':
                self.variable_elements = vic_variables.get_elements(self.ui_locator, var, gvar)
            elif self.ui_by == 'public element':
                self.ui_by, self.ui_locator = web_ui_test.method.get_public_elements(self)

    # 解析表达式
    def analysis_expression(self):
        eval_expression = self.other_data
        variable_dict = vic_variables.get_variable_dict(self.variables, self.global_variables)
        eo = vic_eval.EvalObject(eval_expression, variable_dict, self.logger)
        eval_success, eval_result, final_expression = eo.get_eval_result()
        if eval_success:
            run_result = ['p', '计算表达式：{}\n结果为：{}'.format(final_expression, eval_result)]
        else:
            raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))
        return run_result, eval_success, eval_result, final_expression

    def execute(self):
        self.step_result.start_date = datetime.datetime.now()  # 记录开始执行时的时间

        self.step_result.loop_id = self.loop_id  # 记录循环迭代次数
        self.step_result.save()  # 暂存，防止子用例设置调用步骤时报错
        drs = self.drs = self.vic_case.driver_container  # 获取运行时driver
        dr = drs.get("web_dr", None)
        # 简称
        estr = self.execute_str
        vc = self.vic_case
        var = self.variables
        gvar = self.global_variables
        logger = self.logger
        ac = self.action_code
        atc = self.action_type_code
        timeout = self.timeout

        try:
            self.pause_()

            # selenium驱动初始化检查
            if atc == 'WEB-UI':
                web_ui_test.method.check_web_driver(self)
                dr = drs.get("web_dr", None)
                web_ui_test.method.set_driver_timeout(dr, timeout)

            # 如果步骤执行过程中页面元素被改变导致出现StaleElementReferenceException，将自动再次执行步骤
            start_time = time.time()
            re_run = True
            re_run_count = 0
            elapsed_time = 0
            pause_time = 0
            while re_run and not self.force_stop:
                re_run = False
                try:
                    # 非重跑时才进行逻辑判断
                    if re_run_count == 0:
                        # 分支判断 - 如果
                        if ac == 'OTHER_IF':
                            self.update_test_data('other_data')
                            _step_active = vc.step_active
                            # 如果当前步骤处于激活状态
                            if _step_active:
                                # 解析表达式
                                if not self.other_data:
                                    raise ValueError('未提供表达式')
                                run_result, _, eval_result, _ = self.analysis_expression()
                                if eval_result is True:
                                    run_result[1] = '{}\n表达式为真，进入分支'.format(run_result[1])
                                    _result = True
                                else:
                                    run_result[1] = '{}\n表达式为假，跳过分支'.format(run_result[1])
                                    _result = False
                                self.run_result = run_result
                                # 匹配成功则开始执行后续步骤
                                vc.step_active = _result
                            else:
                                _result = None
                                self.run_result = ['i', '忽略（不记录错误）']

                            # 创建分支对象
                            if_object = {'result': _result, 'active': _step_active}
                            # 添加到分支判断列表
                            vc.if_list.append(if_object)
                        # 分支判断 - 否则如果
                        elif ac == 'OTHER_ELSE_IF':
                            self.update_test_data('other_data')
                            if vc.if_list:
                                # 获取最后一个分支对象
                                if_object = vc.if_list[-1]
                                # 判断当前分支是否被激活
                                if if_object['active']:
                                    # 判断之前有没出现else
                                    if 'else' in if_object:
                                        msg = '“ELSE_IF”不应出现在ELSE之后，请检查用例'
                                        logger.warning('【{}】\t{}'.format(estr, msg))
                                        self.run_result = ['f', msg]
                                        vc.step_active = False
                                    # 如之前的分支已匹配成功
                                    elif if_object['result']:
                                        self.run_result = ['i', '已有符合条件的分支被执行，本分支将被跳过']
                                        vc.step_active = False
                                    else:
                                        # 解析表达式
                                        if not self.other_data:
                                            raise ValueError('未提供表达式')
                                        run_result, _, eval_result, _ = self.analysis_expression()
                                        if eval_result is True:
                                            run_result[1] = '{}\n表达式为真，进入分支'.format(run_result[1])
                                            if_object['result'] = _result = True
                                        else:
                                            run_result[1] = '{}\n表达式为假，跳过分支'.format(run_result[1])
                                            _result = False
                                        self.run_result = run_result

                                        # 匹配成功则开始执行后续步骤
                                        vc.step_active = _result
                                else:
                                    self.run_result = ['i', '忽略（不记录错误）']
                            else:
                                msg = '出现多余的“ELSE_IF”步骤，可能会导致意外的错误，请检查用例'
                                logger.warning('【{}】\t{}'.format(estr, msg))
                                self.run_result = ['f', msg]
                        # 分支判断 - 否则
                        elif ac == 'OTHER_ELSE':
                            msg = '出现多余的“ELSE”步骤，可能会导致意外的错误，请检查用例'
                            if vc.if_list:
                                # 获取最后一个分支对象
                                if_object = vc.if_list[-1]
                                # 判断当前分支是否被激活
                                if if_object['active']:
                                    # 判断是否分支中的第一个else
                                    if 'else' in if_object:
                                        logger.warning('【{}】\t{}'.format(estr, msg))
                                        self.run_result = ['f', msg]
                                        vc.step_active = False
                                    else:
                                        # 反转激活标志
                                        if if_object['result']:
                                            self.run_result = ['i', '已有符合条件的分支被执行，else分支将被跳过']
                                        else:
                                            self.run_result = ['p', '没有找到符合条件的分支，else分支将被执行']
                                        vc.step_active = not if_object['result']
                                        # 在分支对象中添加else标记
                                        if_object['else'] = True
                                else:
                                    self.run_result = ['i', '忽略（不记录错误）']
                            else:
                                logger.warning('【{}】\t{}'.format(estr, msg))
                                self.run_result = ['f', msg]
                        # 分支判断 - 结束
                        elif ac == 'OTHER_END_IF':
                            if vc.if_list:
                                # 获取并删除最后一个分支对象
                                if_object = vc.if_list.pop()
                                # 判断当前分支是否被激活
                                if if_object['active']:
                                    # 后续步骤重置为激活状态
                                    vc.step_active = True
                                else:
                                    self.run_result = ['i', '忽略（不记录错误）']
                            else:
                                msg = '出现多余的“END_IF”步骤，可能会导致意外的错误，请检查用例'
                                logger.warning('【{}】\t{}'.format(estr, msg))
                                self.run_result = ['f', msg]

                        if vc.step_active:
                            # 循环判断 - 开始
                            if ac == 'OTHER_START_LOOP':
                                vc.loop_list.append([self.step_result.step_order - 1, 1])

                            # 循环判断 - 结束
                            elif ac == 'OTHER_END_LOOP':
                                self.update_test_data('other_data')
                                if vc.loop_list:
                                    loop_count = vc.loop_list[-1][1]
                                    if loop_count > LOOP_ITERATIONS_LIMIT-1:
                                        msg = '循环次数超限，强制跳出循环'
                                        logger.warning('【{}】\t{}'.format(estr, msg))
                                        run_result = ['f', msg]
                                        eval_result = False
                                    else:
                                        # 解析表达式
                                        if not self.other_data:
                                            raise ValueError('未提供表达式')
                                        run_result, _, eval_result, _ = self.analysis_expression()

                                    if eval_result is True:
                                        run_result[1] = '{}\n第【{}】次循环结束，表达式为真，进入下一次循环'.format(
                                            run_result[1], loop_count)
                                        vc.loop_list[-1][1] += 1
                                        vc.loop_active = True
                                    else:
                                        # 停止循环
                                        run_result[1] = '{}\n第【{}】次循环结束，跳出循环'.format(run_result[1], loop_count)
                                        vc.loop_list.pop()
                                    self.run_result = run_result
                                else:
                                    msg = '出现多余的“END_LOOP”步骤，可能会导致意外的错误，请检查用例'
                                    logger.warning('【{}】\t{}'.format(estr, msg))
                                    self.run_result = ['f', msg]

                    # 如果步骤为分支判断，那么保留步骤结果文字
                    if vc.step_active or ac in (
                            'OTHER_IF', 'OTHER_ELSE', 'OTHER_ELSE_IF', 'OTHER_END_IF'):
                        if ac in (
                                'OTHER_IF', 'OTHER_ELSE', 'OTHER_ELSE_IF', 'OTHER_END_IF', 'OTHER_START_LOOP',
                                'OTHER_END_LOOP'):
                            pass
                        # ===== UI =====
                        # 处理浏览器弹窗
                        elif ac == 'UI_ALERT_HANDLE':
                            if re_run_count == 0:
                                self.update_test_data('ui_alert_handle_text')
                            self.run_result, _, _, _pause_time = web_ui_test.method.alert_handle(self)
                            pause_time += _pause_time

                        # 打开URL
                        elif ac == 'UI_GO_TO_URL':
                            if re_run_count == 0:
                                self.update_test_data('ui_data')
                            if not self.ui_data:
                                raise ValueError('请提供要打开的URL地址')
                            self.run_result = web_ui_test.method.go_to_url(self)

                        # 刷新页面
                        elif ac == 'UI_REFRESH':
                            dr.refresh()

                        # 前进
                        elif ac == 'UI_FORWARD':
                            dr.forward()

                        # 后退
                        elif ac == 'UI_BACK':
                            dr.back()

                        # 截图
                        elif ac == 'UI_SCREENSHOT':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element', 'ui_data')
                            self.run_result, img, _, _pause_time = web_ui_test.screenshot.get_screenshot(self)
                            pause_time += _pause_time
                            if img:
                                self.img_list.append(img)

                        # 切换frame
                        elif ac == 'UI_SWITCH_TO_FRAME':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element')
                            self.run_result, _, _pause_time = web_ui_test.method.try_to_switch_to_frame(self)
                            pause_time += _pause_time

                        # 退出frame
                        elif ac == 'UI_SWITCH_TO_DEFAULT_CONTENT':
                            dr.switch_to.default_content()

                        # 切换至浏览器的其他窗口或标签
                        elif ac == 'UI_SWITCH_TO_WINDOW':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element', 'ui_data')
                            self.run_result, new_window_handle, _, _pause_time \
                                = web_ui_test.method.try_to_switch_to_window(self)
                            pause_time += _pause_time

                        # 关闭当前浏览器窗口或标签并切换至其他窗口或标签
                        elif ac == 'UI_CLOSE_WINDOW':
                            if len(dr.window_handles) == 1:
                                raise exceptions.InvalidSwitchToTargetException(
                                    '当前窗口是浏览器的最后一个窗口，如果需要关闭浏览器请使用【重置浏览器】步骤')
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element', 'ui_data')
                            try:
                                current_window_handle = dr.current_window_handle
                            except exceptions.NoSuchWindowException:
                                logger.warning('【{}】\t无法获取当前窗口'.format(estr), exc_info=True)
                                current_window_handle = 'N/A'
                            dr.close()
                            self.run_result, new_window_handle, _, _pause_time \
                                = web_ui_test.method.try_to_switch_to_window(self, current_window_handle)
                            pause_time += _pause_time

                        # 重置浏览器
                        elif ac == 'UI_RESET_BROWSER':
                            if dr is not None:
                                try:
                                    dr.quit()
                                except:
                                    logger.warning('【{}】\t有一个浏览器无法关闭，请手动关闭'.format(estr), exc_info=True)
                                del dr
                                logger.info('【{}】\t启动浏览器...'.format(estr))
                                self.dr = dr = web_ui_test.driver.get_driver(self.config, estr, 3, self.timeout, logger=logger)
                                vc.driver_container["web_dr"] = dr

                        # 单击
                        elif ac == 'UI_CLICK':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element')
                            if not self.ui_by or not self.ui_locator:
                                raise ValueError('无效的定位方式或定位符')

                            self.run_result, element, _, _pause_time = web_ui_test.method.try_to_click(self)
                            pause_time += _pause_time
                            self.elements = [element]
                            if self.save_as:
                                var.set_variable(self.save_as, self.elements)

                        # 输入
                        elif ac == 'UI_ENTER':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element', 'ui_data')
                            if not self.ui_by or not self.ui_locator:
                                raise ValueError('无效的定位方式或定位符')

                            self.run_result, element, _, _pause_time = web_ui_test.method.try_to_enter(self)
                            pause_time += _pause_time
                            self.elements = [element]
                            if self.save_as:
                                var.set_variable(self.save_as, self.elements)

                        # 输入
                        elif ac == 'UI_CLEAR':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element')
                            if not self.ui_by or not self.ui_locator:
                                raise ValueError('无效的定位方式或定位符')

                            self.run_result, element, _, _pause_time = web_ui_test.method.try_to_clear(self)
                            pause_time += _pause_time
                            self.elements = [element]
                            if self.save_as:
                                var.set_variable(self.save_as, self.elements)

                        # 选择下拉项
                        elif ac == 'UI_SELECT':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element', 'ui_data')
                            if not self.ui_by or not self.ui_locator:
                                raise ValueError('无效的定位方式或定位符')

                            self.run_result, element, _, _pause_time = web_ui_test.method.try_to_select(self)
                            pause_time += _pause_time
                            self.elements = [element]
                            if self.save_as:
                                var.set_variable(self.save_as, self.elements)

                        # 特殊动作
                        elif ac == 'UI_SPECIAL_ACTION':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element')
                                _update_test_data = True
                            else:
                                _update_test_data = False
                            self.run_result, element, _, _pause_time \
                                = web_ui_test.method.perform_special_action(self, _update_test_data)
                            pause_time += _pause_time
                            self.elements = [element]
                            if self.save_as:
                                var.set_variable(self.save_as, self.elements)

                        # 移动到元素位置
                        elif ac == 'UI_SCROLL_INTO_VIEW':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element')
                            if not self.ui_by or not self.ui_locator:
                                raise ValueError('无效的定位方式或定位符')

                            self.run_result, element, _, _pause_time = web_ui_test.method.try_to_scroll_into_view(self)
                            pause_time = _pause_time
                            self.elements = [element]
                            if self.save_as:
                                var.set_variable(self.save_as, self.elements)

                        # 验证URL
                        elif ac == 'UI_VERIFY_URL':
                            if re_run_count == 0:
                                self.update_test_data('ui_data')
                            if not self.ui_data:
                                raise ValueError('无验证内容')
                            else:
                                self.run_result, _, _pause_time = web_ui_test.method.wait_for_page_redirect(self)
                            pause_time += _pause_time
                            if self.save_as:
                                if self.run_result[0] == 'p':
                                    verify_result = True
                                else:
                                    verify_result = False
                                msg = var.set_variable(self.save_as, verify_result)
                                self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)

                        # 验证文字
                        elif ac == 'UI_VERIFY_TEXT':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element', 'ui_data')
                            if not self.ui_data:
                                raise ValueError('请提供要验证的文字')
                            self.run_result, self.elements, self.fail_elements, _, _pause_time \
                                = web_ui_test.method.wait_for_text_present(self)
                            pause_time += _pause_time
                            if self.save_as:
                                if self.run_result[0] == 'p':
                                    verify_result = True
                                else:
                                    verify_result = False
                                msg = var.set_variable(self.save_as, verify_result)
                                self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)

                        # 验证元素可见
                        elif ac == 'UI_VERIFY_ELEMENT_SHOW':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element', 'ui_data')
                            if not self.ui_by or not self.ui_locator:
                                raise ValueError('无效的定位方式或定位符')

                            self.run_result, self.elements, _, _, _pause_time \
                                = web_ui_test.method.wait_for_element_visible(self)
                            pause_time += _pause_time

                            if self.save_as:
                                if self.run_result[0] == 'p':
                                    verify_result = True
                                else:
                                    verify_result = False
                                msg = var.set_variable(self.save_as, verify_result)
                                self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)

                        # 验证元素隐藏
                        elif ac == 'UI_VERIFY_ELEMENT_HIDE':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element')
                            if not self.ui_by or not self.ui_locator:
                                raise ValueError('无效的定位方式或定位符')

                            self.run_result, self.fail_elements, _, _pause_time \
                                = web_ui_test.method.wait_for_element_disappear(self)
                            pause_time += _pause_time

                            if self.save_as:
                                if self.run_result[0] == 'p':
                                    verify_result = True
                                else:
                                    verify_result = False
                                msg = var.set_variable(self.save_as, verify_result)
                                self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)

                        # 运行JavaScript
                        elif ac == 'UI_EXECUTE_JS':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element', 'ui_data')
                            if not self.ui_data:
                                raise ValueError('未提供javascript代码')

                            self.run_result, js_result, _, _pause_time = web_ui_test.method.run_js(self)
                            pause_time += _pause_time
                            if self.save_as:
                                msg = var.set_variable(self.save_as, js_result)
                                self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)

                        # 验证JavaScript结果
                        elif ac == 'UI_VERIFY_JS_RETURN':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element', 'ui_data')
                            if not self.ui_data:
                                raise ValueError('未提供javascript代码')

                            self.run_result, js_result, _, _pause_time = web_ui_test.method.run_js(self)
                            pause_time += _pause_time
                            if js_result is not True:
                                self.run_result = ['f', self.run_result[1]]
                                verify_result = False
                            else:
                                verify_result = True
                            if self.save_as:
                                msg = var.set_variable(self.save_as, verify_result)
                                self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)

                        # 保存元素变量
                        elif ac == 'UI_SAVE_ELEMENT':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element', 'ui_data')
                            if not self.save_as:
                                raise ValueError('没有提供变量名')
                            if not self.ui_by or not self.ui_locator:
                                raise ValueError('无效的定位方式或定位符')

                            self.run_result, self.elements, _, _pause_time \
                                = web_ui_test.method.wait_for_element_present(self)
                            pause_time += _pause_time

                            if self.run_result[0] == 'p':
                                msg = var.set_variable(self.save_as, self.elements)
                                self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)
                            else:
                                raise exceptions.NoSuchElementException('无法保存变量，{}'.format(self.run_result[1]))

                        # 保存url变量
                        elif ac == 'UI_SAVE_URL':
                            if re_run_count == 0:
                                self.update_test_data('ui_data')
                            if not self.save_as:
                                raise ValueError('没有提供变量名')

                            self.run_result, data_ = web_ui_test.method.get_url(self)

                            if self.run_result[0] == 'p':
                                msg = var.set_variable(self.save_as, data_)
                                self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)
                            else:
                                raise exceptions.WebDriverException('无法保存变量，{}'.format(self.run_result[1]))

                        # 保存元素文本
                        elif ac == 'UI_SAVE_ELEMENT_TEXT':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element')
                            if not self.save_as:
                                raise ValueError('没有提供变量名')
                            if not self.ui_by or not self.ui_locator:
                                raise ValueError('无效的定位方式或定位符')

                            self.run_result, text, _, _pause_time= web_ui_test.method.get_element_text(self)
                            pause_time += _pause_time

                            if self.run_result[0] == 'p':
                                msg = var.set_variable(self.save_as, text)
                                self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)
                            else:
                                raise exceptions.NoSuchElementException('无法保存变量，{}'.format(self.run_result[1]))

                        # 保存元素属性值
                        elif ac == 'UI_SAVE_ELEMENT_ATTR':
                            if re_run_count == 0:
                                self.update_test_data('ui_locator', 'ui_base_element', 'ui_data')
                            if not self.save_as:
                                raise ValueError('没有提供变量名')
                            if not self.ui_by or not self.ui_locator:
                                raise ValueError('无效的定位方式或定位符')

                            self.run_result, text, _, _pause_time = web_ui_test.method.get_element_attr(self)
                            pause_time += _pause_time

                            if self.run_result[0] == 'p':
                                msg = var.set_variable(self.save_as, text)
                                self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)
                            else:
                                raise exceptions.NoSuchAttributeException('无法保存变量，{}'.format(self.run_result[1]))

                        # ===== API =====
                        elif ac == 'API_SEND_HTTP_REQUEST':
                            self.update_test_data(
                                'api_url', 'api_headers', 'api_headers', 'api_body', 'api_decode', 'api_data')
                            if not self.api_url:
                                raise ValueError('请提供请求地址')
                            if self.api_headers:
                                try:
                                    self.api_headers = json.loads(self.api_headers)
                                except json.decoder.JSONDecodeError as e:
                                    raise ValueError('headers格式不正确，请使用正确的json格式。错误信息：{}'.format(
                                        getattr(e, 'msg', str(e))))
                            else:
                                self.api_headers = dict()
                            response, _, _ = api_method.send_http_request(self)
                            if isinstance(response, requests.exceptions.Timeout):
                                self.run_result = ['f', '请求超时']
                            else:
                                try:
                                    pretty_request_header = json.dumps(self.api_headers, indent=2, ensure_ascii=False)
                                except TypeError:
                                    pretty_request_header = str(self.api_headers)
                                pretty_response_header = json.dumps(dict(response.headers), indent=2, ensure_ascii=False)

                                run_result_state = 'p'
                                response_body_msg = response.text

                                if self.api_response_status or self.api_data:
                                    run_result, response_body_msg = api_method.verify_http_response(
                                        self.api_response_status, self.api_data, response, logger)
                                    if run_result[0] == 'p':
                                        prefix_msg = '请求发送完毕，结果验证通过'
                                    else:
                                        run_result_state = 'f'
                                        prefix_msg = '请求发送完毕，结果验证失败'
                                    suffix_msg = '验证结果：\n{}'.format(run_result[1])
                                else:
                                    prefix_msg = '请求发送完毕'
                                    suffix_msg = ''

                                if len(response_body_msg) > 10000:
                                    response_body_msg = '{}\n*****（为节约空间，只保存了前10000个字符）*****'.format(
                                        response_body_msg[:10000])
                                msg = '请求地址：\n{}\n' \
                                      '请求方式：\n{}\n' \
                                      '请求头：\n{}\n' \
                                      '请求体：\n{}\n' \
                                      '响应状态：\n{} {}\n' \
                                      '响应头：\n{}\n' \
                                      '响应体：\n{}\n{}'.format(
                                    self.api_url,
                                    self.api_method,
                                    pretty_request_header,
                                    self.api_body,
                                    response.status_code, response.reason,
                                    pretty_response_header,
                                    response_body_msg, suffix_msg)

                                if self.save_as and self.api_data:
                                    if self.run_result[0] == 'p':
                                        verify_result = True
                                    else:
                                        verify_result = False
                                    _msg = var.set_variable(self.save_as, verify_result)
                                    msg = '{}\n{}'.format(msg, _msg)

                                if self.api_save and self.api_save != '[]':
                                    success, msg_ = api_method.save_http_response(
                                        response, response.text, self.api_save, var, logger=logger)
                                    msg = '{}\n响应内容保存情况：\n{}'.format(msg, msg_)
                                    if not success:
                                        run_result_state = 'f'
                                        prefix_msg = '{}，响应内容保存失败'.format(prefix_msg)

                                msg = '{}\n{}'.format(prefix_msg, msg)
                                self.run_result = [run_result_state, msg]

                                if self.save_as:
                                    if self.run_result[0] == 'p':
                                        verify_result = True
                                    else:
                                        verify_result = False
                                    msg = var.set_variable(self.save_as, verify_result)
                                    self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)

                        # ===== DB =====
                        elif ac == 'DB_EXECUTE_SQL':
                            self.update_test_data(
                                'db_host', 'db_port', 'db_name', 'db_user', 'db_password', 'db_lang', 'db_sql')
                            try:
                                sql_result, select_result = db_method.get_sql_result(self)
                            except:
                                logger.warning('【{}】\t连接数据库或SQL执行报错\nSQL语句：\n{}'.format(
                                    estr, self.db_sql), exc_info=True)
                                e_str = traceback.format_exc()
                                self.run_result = ['f', '连接数据库或SQL执行报错\nSQL语句：\n{}\n{}'.format(
                                    self.db_sql, e_str)]
                            else:
                                try:
                                    pretty_result = json.dumps(
                                        select_result, indent=2, ensure_ascii=False, cls=db_method.JsonDatetimeEncoder)
                                except TypeError:
                                    pretty_result = str(select_result)
                                if len(pretty_result) > 10000:
                                    pretty_result = '{}\n*****（为节约空间，测试结果只保存前10000个字符）*****'.format(pretty_result[:10000])

                                run_result_state = 'p'
                                msg = 'SQL执行完毕\nSQL语句：\n{}\n{}\n结果集：\n{}'.format(
                                    self.db_sql, sql_result, pretty_result)

                                if self.save_as:
                                    _msg = var.set_variable(self.save_as, select_result)
                                    msg = '{}\n{}'.format(msg, _msg)
                                self.run_result = [run_result_state, msg]

                        elif ac == 'DB_VERIFY_SQL_RESULT':
                            self.update_test_data(
                                'db_host', 'db_port', 'db_name', 'db_user', 'db_password', 'db_lang', 'db_sql',
                                'db_data')
                            if not self.db_data:
                                raise ValueError('未提供验证内容，如无需验证，请使用【执行SQL】动作')
                            try:
                                sql_result, select_result = db_method.get_sql_result(self)
                            except:
                                logger.warning('【{}】\t连接数据库或SQL执行报错\nSQL语句：\n{}'.format(
                                    estr, self.db_sql), exc_info=True)
                                e_str = traceback.format_exc()
                                self.run_result = ['f', '连接数据库或SQL执行报错\nSQL语句：\n{}\n{}'.format(
                                    self.db_sql, e_str)]
                            else:
                                try:
                                    pretty_result = json.dumps(
                                        select_result, indent=2, ensure_ascii=False, cls=db_method.JsonDatetimeEncoder)
                                except TypeError:
                                    pretty_result = str(select_result)
                                if len(pretty_result) > 10000:
                                    pretty_result = '{}\n*****（为节约空间，测试结果只保存前10000个字符）*****'.format(pretty_result[:10000])

                                run_result = db_method.verify_db_test_result(
                                    expect=self.db_data, result=select_result, logger=logger)
                                if run_result[0] == 'p':
                                    run_result_state = 'p'
                                    msg = 'SQL执行完毕，结果验证通过\nSQL语句：\n{}\n{}\n结果集：\n{}'.format(
                                        self.db_sql, sql_result, pretty_result)
                                else:
                                    run_result_state = 'f'
                                    msg = 'SQL执行完毕，结果验证失败\nSQL语句：\n{}\n{}\n结果集：\n{}'.format(
                                        self.db_sql, sql_result, pretty_result)
                                    if run_result[1].error_msg:
                                        '{}\n在查找过程中出现错误：{}'.format(msg, run_result[1].error_msg)

                                self.run_result = [run_result_state, msg]

                                if self.save_as:
                                    if self.run_result[0] == 'p':
                                        verify_result = True
                                    else:
                                        verify_result = False
                                    msg = var.set_variable(self.save_as, verify_result)
                                    self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)

                        # ===== OTHER =====
                        # 等待
                        elif ac == 'OTHER_SLEEP':
                            if re_run_count == 0:
                                self.update_test_data('other_data')
                            if not self.other_data:
                                raise ValueError('未提供等待时间')
                            try:
                                _timeout = float(self.other_data)
                            except (ValueError, TypeError):
                                raise ValueError('【{}】无法转换为数字'.format(self.other_data))

                            vc.vic_suite.vic_cases[vc.case_order-1].pause_signal = True  # 向一级用例发送暂停信号
                            self.pause_(_timeout, '【{}】\t已等待【{}】秒，剩余{}秒')

                            # for i in range(int(_timeout[1])):
                            #     if self.force_stop:
                            #         break
                            #     self.pause_()
                            #     time.sleep(1)
                            #     logger.info('【{}】\t已等待【{}】秒'.format(estr, i + 1))
                            # time.sleep(_timeout[0])  # 补上小数部分

                        # 保存用例变量
                        elif ac == 'OTHER_SAVE_CASE_VARIABLE':
                            if re_run_count == 0:
                                self.update_test_data('other_data')
                            if not self.save_as:
                                raise ValueError('没有提供变量名')
                            elif not self.other_data:
                                raise ValueError('没有提供表达式')
                            else:
                                eo = vic_eval.EvalObject(
                                    self.other_data, vic_variables.get_variable_dict(var, gvar), logger)
                                eval_success, eval_result, final_expression = eo.get_eval_result()
                                if eval_success:
                                    msg = var.set_variable(self.save_as, eval_result)
                                    self.run_result = ['p', '计算表达式：{}\n结果为：{}\n{}'.format(
                                        final_expression, eval_result, msg)]
                                else:
                                    raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))

                        # 保存全局变量
                        elif ac == 'OTHER_SAVE_GLOBAL_VARIABLE':
                            if re_run_count == 0:
                                self.update_test_data('other_data')
                            if not self.save_as:
                                raise ValueError('没有提供变量名')
                            elif not self.other_data:
                                raise ValueError('没有提供表达式')
                            else:
                                eo = vic_eval.EvalObject(
                                    self.other_data, vic_variables.get_variable_dict(var, gvar), logger)
                                eval_success, eval_result, final_expression = eo.get_eval_result()
                                if eval_success:
                                    msg = gvar.set_variable(self.save_as, eval_result)
                                    self.run_result = ['p', '计算表达式：{}\n结果为：{}\n全局{}'.format(
                                        final_expression, eval_result, msg)]
                                else:
                                    raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))

                        # 转换变量类型
                        elif ac == 'OTHER_CHANGE_VARIABLE_TYPE':
                            if self.other_data not in ('str', 'int', 'float', 'bool', 'time', 'datetime'):
                                raise ValueError('无效的转换类型【{}】'.format(self.other_data))
                            found, variable = vic_variables.get_variable(self.save_as, var, gvar)
                            if not found:
                                raise ValueError('找不到名为【{}】的变量'.format(self.save_as))
                            try:
                                _msg = '变量类型转换为'
                                if self.other_data == 'str':
                                    variable = str(variable)
                                    _msg = '{}字符串'.format(_msg)
                                elif self.other_data == 'int':
                                    variable = int(variable)
                                    _msg = '{}整型'.format(_msg)
                                elif self.other_data == 'float':
                                    variable = float(variable)
                                    _msg = '{}浮点型'.format(_msg)
                                elif self.other_data == 'bool':
                                    variable = bool(variable)
                                    _msg = '{}布尔型'.format(_msg)
                                elif self.other_data in ('time', 'datetime'):
                                    variable = vic_date_handle.str_to_time(str(variable))
                                    _msg = '{}日期型'.format(_msg)
                            except (ValueError, TypeError) as e:
                                raise ValueError('变量类型转换失败，错误信息：{}'.format(e))
                            else:
                                if found == 'local':
                                    msg = var.set_variable(self.save_as, variable)
                                else:
                                    msg = gvar.set_variable(self.save_as, variable)
                                    msg = '全局{}'.format(msg)
                                msg = '{}，{}'.format(_msg, msg)
                                self.run_result = ['p', msg]

                        # 使用正则表达式截取变量
                        elif ac == 'OTHER_GET_VALUE_WITH_RE':
                            if re_run_count == 0:
                                self.update_test_data('other_data')
                            if self.other_data == '':
                                raise ValueError('没有提供表达式')
                            found, variable = vic_variables.get_variable(self.save_as, var, gvar)
                            if not found:
                                raise ValueError('找不到名为【{}】的变量'.format(self.save_as))
                            find_result = vic_find_object.find_with_condition(self.other_data, variable, logger=logger)
                            if find_result.is_matched and find_result.re_result:
                                variable = vic_find_object.get_first_str_in_re_result(find_result.re_result)
                                msg = '变量【{}】被截取为【{}】'.format(self.save_as, variable)
                                if found == 'local':
                                    var.set_variable(self.save_as, variable)
                                else:
                                    gvar.set_variable(self.save_as, variable)
                                    msg = '全局{}'.format(msg)
                                self.run_result = ['p', msg]
                            else:
                                msg = '无法匹配给定的正则表达式，所以变量【{}】的值没有改变'.format(self.save_as, variable)
                                if find_result.error_msg:
                                    msg = '{}\n在查找过程中出现错误：{}'.format(msg, find_result.error_msg)
                                self.run_result = ['f', msg]

                        # 验证表达式
                        elif ac == 'OTHER_VERIFY_EXPRESSION':
                            if re_run_count == 0:
                                self.update_test_data('other_data')
                            if self.other_data == '':
                                raise ValueError('未提供表达式')
                            eo = vic_eval.EvalObject(
                                self.other_data, vic_variables.get_variable_dict(var, gvar),
                                logger)
                            eval_success, eval_result, final_expression = eo.get_eval_result()
                            if eval_success:
                                if eval_result is True:
                                    self.run_result = ['p', '计算表达式：{}\n结果为：{}'.format(final_expression, eval_result)]
                                else:
                                    self.run_result = ['f', '计算表达式：{}\n结果为：{}'.format(final_expression, eval_result)]
                            else:
                                raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))

                            if self.save_as:
                                if self.run_result[0] == 'p':
                                    verify_result = True
                                else:
                                    verify_result = False
                                msg = var.set_variable(self.save_as, verify_result)
                                self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)

                        # 调用子用例
                        elif ac == 'OTHER_CALL_SUB_CASE':
                            if self.other_sub_case is None:
                                raise ValueError('子用例为空或不存在')
                            elif self.other_sub_case.pk in vc.parent_case_pk_list:
                                raise RecursionError('子用例[ID:{}]【{}】被递归调用'.format(
                                    self.other_sub_case.pk, self.other_sub_case.name))
                            else:
                                from .vic_case import VicCase
                                sub_case = VicCase(
                                    case=self.other_sub_case,
                                    case_order=vc.case_order,
                                    vic_suite=vc.vic_suite,
                                    execute_str=estr,
                                    variables=var,
                                    vic_step=self,
                                    parent_case_pk_list=vc.parent_case_pk_list,
                                    driver_container=vc.driver_container
                                )
                                sub_case.execute()
                                case_result_ = sub_case.case_result
                                # 更新driver
                                self.drs = self.vic_case.driver_container = sub_case.driver_container
                                self.step_result.has_sub_case = True
                                if case_result_.error_count or case_result_.result_error:
                                    self.run_result = ['e', '子用例执行出错，请查看子用例中步骤的执行结果']
                                elif case_result_.fail_count:
                                    self.run_result = ['f', '子用例验证失败，请查看子用例中步骤的执行结果']
                                elif case_result_.execute_count == 0:
                                    self.run_result = ['i', '子用例未执行']
                                else:
                                    self.run_result = ['p', '子用例执行成功']

                                if self.save_as:
                                    if self.run_result[0] == 'p':
                                        verify_result = True
                                    else:
                                        verify_result = False
                                    msg = var.set_variable(self.save_as, verify_result)
                                    self.run_result[1] = '{}\n==========\n{}'.format(self.run_result[1], msg)
                                if self.run_result[0] == 'e':
                                    raise RuntimeError('子用例出现错误，请查看子用例中步骤的执行结果')

                        # 无效的关键字
                        else:
                            raise exceptions.UnknownMethodException('未知的动作代码【{}】'.format(ac))

                        # 判断是否出现浏览器弹窗
                        if atc == 'WEB-UI' and dr is not None:
                            try:
                                # 防止切换窗口后页面还未加载完毕就获取弹窗导致超时
                                if ac in ['UI_SWITCH_TO_WINDOW', 'UI_CLOSE_WINDOW']:
                                    try:
                                        logger.debug(f"======= {dr.command_executor.get_timeout()=} ========")
                                        dr.find_elements(By.TAG_NAME, 'body')
                                    except exceptions.UnexpectedAlertPresentException:
                                        pass
                                web_ui_test.method.set_driver_timeout(dr, 5)
                                alert_ = dr.switch_to.alert
                                self.browser_alert = True
                                self.browser_alert_text = alert_.text
                            except exceptions.NoAlertPresentException:
                                pass
                            except exceptions.TimeoutException:
                                self.socket_no_response = True
                                raise
                            else:
                                self.socket_no_response = False
                            finally:
                                web_ui_test.method.set_driver_timeout(dr, timeout)

                        # 获取UI验证截图
                        if 'UI_VERIFY_' in ac:
                            if self.browser_alert:
                                logger.warning(
                                    '【{}】\t无法获取UI验证截图，因为出现浏览器弹窗导致浏览器被锁死，内容为：{}'.format(
                                        estr, self.browser_alert_text))
                            else:
                                if self.ui_get_ss:
                                    highlight_elements_map = {}
                                    if self.elements:
                                        highlight_elements_map = web_ui_test.method.highlight(dr, self.elements, 'green')
                                    if self.fail_elements:
                                        highlight_elements_map = {
                                            **highlight_elements_map,
                                            **web_ui_test.method.highlight(dr, self.fail_elements, 'red')
                                        }
                                    _start_time = time.time()
                                    _pause_time = 0
                                    try:
                                        _ui_by = self.ui_by
                                        _ui_locator = self.ui_locator
                                        self.ui_by = None
                                        self.ui_locator = None
                                        _, img, _, _pause_time = web_ui_test.screenshot.get_screenshot(self)
                                        if img:
                                            self.img_list.append(img)
                                        self.ui_by = _ui_by
                                        self.ui_locator = _ui_locator
                                    except Exception:
                                        logger.warning('【{}】\t无法获取UI验证截图'.format(estr), exc_info=True)
                                        _pause_time = time.time() - _start_time
                                    finally:
                                        pause_time += _pause_time
                                    if highlight_elements_map:
                                        web_ui_test.method.cancel_highlight(dr, highlight_elements_map)
                                else:
                                    if self.elements:
                                        web_ui_test.method.highlight_for_a_moment(dr, self.elements, 'green', sleep=0.5)
                                    if self.fail_elements:
                                        web_ui_test.method.highlight_for_a_moment(dr, self.fail_elements, 'red', sleep=0.5)

                        # 通过添加步骤间等待时间控制UI测试执行速度
                        if atc == 'WEB-UI' and self.ui_step_interval:
                            _timeout = math.modf(float(self.ui_step_interval))
                            x = int(_timeout[1])
                            for i in range(x):
                                if self.force_stop:
                                    break
                                time.sleep(1)
                                y = i + 1
                                logger.info('【{}】\t步骤间已停顿{}秒，剩余{}秒'.format(estr, y, x-y))
                            time.sleep(_timeout[0])  # 补上小数部分
                    else:
                        self.run_result = ['i', '忽略（不记录错误）']
                # 如果遇到元素过期，将尝试重跑该步骤，直到超时
                except (exceptions.StaleElementReferenceException, exceptions.WebDriverException) as e:
                    if self.force_stop or (time.time() - start_time - pause_time) > timeout:
                        raise
                    _err_msg = 'element is not attached to the page document'
                    if isinstance(e, exceptions.StaleElementReferenceException) or _err_msg in e.msg:
                        re_run = True
                        re_run_count += 1
                        logger.warning('【{}】\t元素已过期，可能是由于页面异步刷新导致，将尝试重新获取元素'.format(estr))
                    else:
                        raise

            if self.force_stop:
                self.step_result.result_state = 4
                self.run_result[1] = '执行中止，中止前信息如下：\n{}'.format(self.run_result[1])
            elif self.run_result[0] == 'i':
                self.step_result.result_state = 0
            elif self.run_result[0] == 'p':
                self.step_result.result_state = 1
            else:
                self.step_result.result_state = 2
            self.step_result.result_message = self.run_result[1]

        except socket_timeout_error:
            self.socket_no_response = True
            logger.error('【{}】\t浏览器响应超时'.format(estr), exc_info=True)
            self.step_result.result_state = 3
            self.step_result.result_message = '浏览器响应超时，请检查网络连接或驱动位于的浏览器窗口是否被关闭'
            self.step_result.result_error = traceback.format_exc()
        except exceptions.TimeoutException:
            logger.error('【{}】\t超时'.format(estr), exc_info=True)
            self.step_result.result_state = 3
            self.step_result.result_message = '执行超时，请增大超时值'
            self.step_result.result_error = traceback.format_exc()
        except exceptions.InvalidSelectorException:
            logger.error('【{}】\t定位符【{}】无效'.format(estr, self.ui_locator), exc_info=True)
            self.step_result.result_state = 3
            self.step_result.result_message = '定位信息【By:{}|Locator:{}】无效'.format(self.ui_by, self.ui_locator)
            self.step_result.result_error = traceback.format_exc()
        except exceptions.UnexpectedAlertPresentException:
            self.browser_alert = True
            alert_ = dr.switch_to.alert
            self.browser_alert_text = alert_.text
            msg = '出现浏览器弹窗导致浏览器被锁死，弹窗内容：{}'.format(self.browser_alert_text)
            logger.error('【{}】\t{}'.format(estr, msg), exc_info=True)
            self.step_result.result_state = 3
            self.step_result.result_message = msg
            self.step_result.result_error = traceback.format_exc()
        except Exception as e:
            logger.error('【{}】\t出错 => {}'.format(estr, getattr(e, 'msg', str(e))), exc_info=True)
            if self.run_result[0] == 'e':
                msg = self.run_result[1]
            else:
                msg = '执行出错：{}'.format(getattr(e, 'msg', str(e)))
            self.step_result.result_state = 3
            self.step_result.result_message = msg
            self.step_result.result_error = traceback.format_exc()

        if atc == 'WEB-UI' and dr is not None:
            if self.socket_no_response:
                self.step_result.ui_last_url = '由于浏览器响应超时，URL获取失败'
                logger.warning('【{}】\t由于浏览器响应超时，无法获取报错时的URL和截图'.format(estr))
            else:
                # 获取当前URL
                try:
                    last_url = dr.current_url
                    self.step_result.ui_last_url = last_url if last_url != 'data:,' else ''
                except exceptions.UnexpectedAlertPresentException:
                    alert_ = dr.switch_to.alert
                    self.browser_alert_text = alert_.text
                    msg = 'URL获取失败，因为出现浏览器弹窗导致浏览器被锁死，弹窗内容：{}'.format(self.browser_alert_text)
                    logger.warning('【{}】\t{}'.format(estr, msg))
                    self.step_result.ui_last_url = msg
                    self.browser_alert = True
                except socket_timeout_error as e:
                    self.socket_no_response = True
                    _msg = 'URL获取失败：{}'.format(getattr(e, 'msg', str(e)))
                    logger.warning('【{}】\t{}'.format(estr, _msg), exc_info=True)
                    self.step_result.ui_last_url = _msg
                except Exception as e:
                    _msg = 'URL获取失败：{}'.format(getattr(e, 'msg', str(e)))
                    logger.warning('【{}】\t{}'.format(estr, _msg), exc_info=True)
                    self.step_result.ui_last_url = _msg

            # 获取报错时截图
            if not self.socket_no_response and self.ui_get_ss and self.step_result.result_state == 3:
                try:
                    self.ui_by = None
                    self.ui_locator = None
                    self.run_result, img, _, _ = web_ui_test.screenshot.get_screenshot(self)
                    if img:
                        self.img_list.append(img)
                except exceptions.UnexpectedAlertPresentException:
                    alert_ = dr.switch_to.alert
                    self.browser_alert_text = alert_.text
                    msg = '截图失败，因为出现浏览器弹窗导致浏览器被锁死，弹窗内容：{}'.format(self.browser_alert_text)
                    logger.warning('【{}】\t{}'.format(estr, msg))
                except:
                    logger.warning('【{}】\t截图失败'.format(estr))

        # 关联截图
        for img in self.img_list:
            self.step_result.imgs.add(img)

        self.step_result.end_date = datetime.datetime.now()
        self.step_result.save()

        return self
