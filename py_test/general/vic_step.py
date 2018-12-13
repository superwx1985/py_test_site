import datetime
import time
import json
import traceback
import uuid
import logging
from socket import timeout as socket_timeout_error
from django.forms.models import model_to_dict
from selenium.common import exceptions
from py_test.general import vic_variables, vic_method
from py_test.vic_tools import vic_find_object
from py_test import ui_test
from py_test.api_test import method as api_method
from py_test.db_test import method as db_method
from py_test.vic_tools import vic_eval, vic_date_handle
from main.models import StepResult, Step
from utils.system import FORCE_STOP


class VicStep:
    def __init__(
            self, step, case_result, step_order, user, execute_str, execute_uuid=uuid.uuid1(), websocket_sender=None):
        self.logger = logging.getLogger('py_test.{}'.format(execute_uuid))

        self.step = step
        self.case_result = case_result
        self.user = user
        self.execute_uuid = execute_uuid
        self.websocket_sender = websocket_sender

        self.id = step.pk
        self.name = step.name
        self.action_type_code = step.action.type.code
        self.action_code = step.action.code

        self.execute_id = '{}-{}'.format(execute_str, step_order)
        self.loop_id = ''
        # 截图列表
        self.img_list = list()

        # 驱动停止响应标志
        self.socket_no_response = False

        self.run_result = ['p', '执行成功']
        self.elements = list()
        self.fail_elements = list()

        # 初始化result数据库对象
        self.step_result = StepResult(
            name=step.name,
            description=step.description,
            keyword=step.keyword,
            action=step.action.full_name,

            case_result=case_result,
            step=step,
            step_order=step_order,
            creator=user,

            result_message='',
            result_error='',
            ui_last_url='',

            snapshot=json.dumps(model_to_dict(step)) if step else None,
        )

        try:
            self.timeout = step.timeout if step.timeout else case_result.suite_result.timeout
            self.ui_get_ss = case_result.suite_result.ui_get_ss
            self.save_as = step.save_as

            ui_by_dict = {i[0]: i[1] for i in Step.ui_by_list}
            self.ui_by = ui_by_dict[step.ui_by]
            self.ui_locator = step.ui_locator
            self.ui_index = step.ui_index
            self.ui_base_element = step.ui_base_element
            self.ui_data = step.ui_data
            ui_special_action_dict = {i[0]: i[2] for i in Step.ui_special_action_list_}
            self.ui_special_action = ui_special_action_dict[step.ui_special_action]
            ui_alert_handle_dict = {i[0]: i[2] for i in Step.ui_alert_handle_list_}
            self.ui_alert_handle = ui_alert_handle_dict.get(step.ui_alert_handle, 'accept')

            self.api_url = step.api_url
            api_method_dict = {i[0]: i[1] for i in Step.api_method_list}
            self.api_method = api_method_dict[step.api_method]
            self.api_headers = step.api_headers
            self.api_body = step.api_body
            self.api_decode = step.api_decode
            self.api_data = step.api_data
            self.api_save = step.api_save

            self.other_data = step.other_data
            self.other_sub_case = step.other_sub_case

            self.db_type = step.db_type
            self.db_host = step.db_host
            self.db_port = step.db_port
            self.db_name = step.db_name
            self.db_user = step.db_user
            self.db_password = step.db_password
            self.db_lang = step.db_lang
            self.db_sql = step.db_sql
            self.db_data = step.db_data
        except Exception as e:
            self.logger.info('【{}】\t步骤读取出错'.format(self.execute_id), exc_info=True)
            self.step_result.result_status = 3
            self.step_result.result_message = '步骤读取出错：{}'.format(getattr(e, 'msg', str(e)))
            self.step_result.result_error = traceback.format_exc()
            raise

    def execute(self, vic_case, global_variables, public_elements):
        # 记录开始执行时的时间
        self.step_result.start_date = datetime.datetime.now()
        # 记录循环迭代次数
        self.step_result.loop_id = self.loop_id
        # 暂存，防止子用例设置调用步骤时报错
        self.step_result.save()

        # 获取driver
        dr = vic_case.driver_container[0]

        ui_locator = ''
        try:
            # 根据当前变量组替换数据
            ui_locator = str(vic_method.replace_special_value(self.ui_locator, vic_case.variables, global_variables, self.logger))
            ui_base_element = str(vic_method.replace_special_value(self.ui_base_element, vic_case.variables, global_variables, self.logger))
            ui_base_element = vic_variables.get_elements(ui_base_element, vic_case.variables, global_variables)[0] if ui_base_element != '' else None
            ui_data = str(vic_method.replace_special_value(self.ui_data, vic_case.variables, global_variables, self.logger))
            other_data = str(vic_method.replace_special_value(self.other_data, vic_case.variables, global_variables, self.logger))

            api_url = str(vic_method.replace_special_value(self.api_url, vic_case.variables, global_variables, self.logger))
            api_headers = str(vic_method.replace_special_value(self.api_headers, vic_case.variables, global_variables, self.logger))
            api_body = str(vic_method.replace_special_value(self.api_body, vic_case.variables, global_variables, self.logger))
            api_decode = str(vic_method.replace_special_value(self.api_decode, vic_case.variables, global_variables, self.logger))
            api_data = str(vic_method.replace_special_value(self.api_data, vic_case.variables, global_variables, self.logger))

            db_host = str(vic_method.replace_special_value(self.db_host, vic_case.variables, global_variables, self.logger))
            db_port = str(vic_method.replace_special_value(self.db_port, vic_case.variables, global_variables, self.logger))
            db_name = str(vic_method.replace_special_value(self.db_name, vic_case.variables, global_variables, self.logger))
            db_user = str(vic_method.replace_special_value(self.db_user, vic_case.variables, global_variables, self.logger))
            db_password = str(vic_method.replace_special_value(self.db_password, vic_case.variables, global_variables, self.logger))
            db_lang = str(vic_method.replace_special_value(self.db_lang, vic_case.variables, global_variables, self.logger))
            db_sql = str(vic_method.replace_special_value(self.db_sql, vic_case.variables, global_variables, self.logger))
            db_data = str(vic_method.replace_special_value(self.db_data, vic_case.variables, global_variables, self.logger))

            # selenium驱动初始化检查
            if self.action_type_code == 'UI':
                if dr is None:
                    raise exceptions.WebDriverException('浏览器未初始化，请检查是否配置有误或浏览器被意外关闭')

            # 设置selenium驱动超时
            if dr:
                # 设置selenium超时时间
                dr.implicitly_wait(self.timeout)
                dr.set_page_load_timeout(self.timeout)
                dr.set_script_timeout(self.timeout)
                # 设置Remote Connection超时时间
                try:
                    _conn = getattr(dr.command_executor, '_conn')
                    _conn.timeout = int(self.timeout + 5)
                except AttributeError:
                    dr.command_executor.set_timeout(int(self.timeout + 5))

            # 如果步骤执行过程中页面元素被改变导致出现StaleElementReferenceException，将自动再次执行步骤
            start_time = time.time()
            re_run = True
            re_run_count = 0
            while re_run:
                re_run = False
                try:
                    # 非重跑时才进行逻辑判断
                    if re_run_count == 0:
                        # 分支判断 - 如果
                        if self.action_code == 'OTHER_IF':
                            _step_active = vic_case.step_active
                            # 如果当前步骤处于激活状态
                            if _step_active:
                                # 解析表达式
                                if other_data == '':
                                    raise ValueError('未提供表达式')
                                run_result, _, eval_result, _ = ui_test.method.analysis_expression(
                                    other_data,
                                    vic_variables.get_variable_dict(vic_case.variables, global_variables),
                                    self.logger
                                )
                                if eval_result is True:
                                    run_result[1] = '{}\n表达式为真，进入分支'.format(run_result[1])
                                    _result = True
                                else:
                                    run_result[1] = '{}\n表达式为假，跳过分支'.format(run_result[1])
                                    _result = False
                                self.run_result = run_result
                                # 匹配成功则开始执行后续步骤
                                vic_case.step_active = _result
                            else:
                                _result = None
                                self.run_result = ['s', '步骤被跳过']

                            # 创建分支对象
                            if_object = {'result': _result, 'active': _step_active}
                            # 添加到分支判断列表
                            vic_case.if_list.append(if_object)

                        # 分支判断 - 否则如果
                        elif self.action_code == 'OTHER_ELSE_IF':
                            if vic_case.if_list:
                                # 获取最后一个分支对象
                                if_object = vic_case.if_list[-1]
                                # 判断当前分支是否被激活
                                if if_object['active']:
                                    # 判断之前有没出现else
                                    if 'else' in if_object:
                                        msg = '“ELSE_IF”不应出现在ELSE之后，请检查用例'
                                        self.logger.warning('【{}】\t{}'.format(self.execute_id, msg))
                                        self.run_result = ['f', msg]
                                        vic_case.step_active = False
                                    # 如之前的分支已匹配成功
                                    elif if_object['result']:
                                        self.run_result = ['s', '已有符合条件的分支被执行，本分支将被跳过']
                                        vic_case.step_active = False
                                    else:
                                        # 解析表达式
                                        if other_data == '':
                                            raise ValueError('未提供表达式')
                                        run_result, _, eval_result, _ = ui_test.method.analysis_expression(
                                            other_data,
                                            vic_variables.get_variable_dict(vic_case.variables, global_variables),
                                            self.logger
                                        )
                                        if eval_result is True:
                                            run_result[1] = '{}\n表达式为真，进入分支'.format(run_result[1])
                                            if_object['result'] = _result = True
                                        else:
                                            run_result[1] = '{}\n表达式为假，跳过分支'.format(run_result[1])
                                            _result = False
                                        self.run_result = run_result

                                        # 匹配成功则开始执行后续步骤
                                        vic_case.step_active = _result
                                else:
                                    self.run_result = ['s', '步骤被跳过']
                            else:
                                msg = '出现多余的“ELSE_IF”步骤，可能会导致意外的错误，请检查用例'
                                self.logger.warning('【{}】\t{}'.format(self.execute_id, msg))
                                self.run_result = ['f', msg]
                        # 分支判断 - 否则
                        elif self.action_code == 'OTHER_ELSE':
                            msg = '出现多余的“ELSE”步骤，可能会导致意外的错误，请检查用例'
                            if vic_case.if_list:
                                # 获取最后一个分支对象
                                if_object = vic_case.if_list[-1]
                                # 判断当前分支是否被激活
                                if if_object['active']:
                                    # 判断是否分支中的第一个else
                                    if 'else' in if_object:
                                        self.logger.warning('【{}】\t{}'.format(self.execute_id, msg))
                                        self.run_result = ['f', msg]
                                        vic_case.step_active = False
                                    else:
                                        # 反转激活标志
                                        if if_object['result']:
                                            self.run_result = ['s', '已有符合条件的分支被执行，else分支将被跳过']
                                        else:
                                            self.run_result = ['p', '没有找到符合条件的分支，else分支将被执行']
                                        vic_case.step_active = not if_object['result']
                                        # 在分支对象中添加else标记
                                        if_object['else'] = True
                                else:
                                    self.run_result = ['s', '步骤被跳过']
                            else:
                                self.logger.warning('【{}】\t{}'.format(self.execute_id, msg))
                                self.run_result = ['f', msg]
                        # 分支判断 - 结束
                        elif self.action_code == 'OTHER_END_IF':
                            if vic_case.if_list:
                                # 获取并删除最后一个分支对象
                                if_object = vic_case.if_list.pop()
                                # 判断当前分支是否被激活
                                if if_object['active']:
                                    # 后续步骤重置为激活状态
                                    vic_case.step_active = True
                                else:
                                    self.run_result = ['s', '步骤被跳过']
                            else:
                                msg = '出现多余的“END_IF”步骤，可能会导致意外的错误，请检查用例'
                                self.logger.warning('【{}】\t{}'.format(self.execute_id, msg))
                                self.run_result = ['f', msg]

                        if vic_case.step_active:
                            # 循环判断 - 开始
                            if self.action_code == 'OTHER_START_LOOP':
                                vic_case.loop_list.append([self.step_result.step_order - 1, 1])

                            # 循环判断 - 结束
                            elif self.action_code == 'OTHER_END_LOOP':
                                if vic_case.loop_list:
                                    loop_count = vic_case.loop_list[-1][1]
                                    if loop_count > 9:
                                        msg = '循环次数超限，强制跳出循环'
                                        self.logger.warning('【{}】\t{}'.format(self.execute_id, msg))
                                        run_result = ['f', msg]
                                        eval_result = False
                                    else:
                                        # 解析表达式
                                        if other_data == '':
                                            raise ValueError('未提供表达式')
                                        run_result, _, eval_result, _ = ui_test.method.analysis_expression(
                                            other_data,
                                            vic_variables.get_variable_dict(vic_case.variables, global_variables),
                                            self.logger
                                        )

                                    if eval_result is True:
                                        run_result[1] = '{}\n第【{}】次循环结束，表达式为真，进入下一次循环'.format(
                                            run_result[1], loop_count)
                                        vic_case.loop_list[-1][1] += 1
                                        vic_case.loop_active = True
                                    else:
                                        # 停止循环
                                        run_result[1] = '{}\n第【{}】次循环结束，跳出循环'.format(run_result[1], loop_count)
                                        vic_case.loop_list.pop()
                                    self.run_result = run_result
                                else:
                                    msg = '出现多余的“END_LOOP”步骤，可能会导致意外的错误，请检查用例'
                                    self.logger.warning('【{}】\t{}'.format(self.execute_id, msg))
                                    self.run_result = ['f', msg]

                    if vic_case.step_active or self.action_code in (
                            'OTHER_IF', 'OTHER_ELSE', 'OTHER_ELSE_IF', 'OTHER_END_IF'):
                        if self.action_code in (
                                'OTHER_IF', 'OTHER_ELSE', 'OTHER_ELSE_IF', 'OTHER_END_IF', 'OTHER_START_LOOP',
                                'OTHER_END_LOOP'):
                            pass
                        # ===== UI =====
                        # 打开URL
                        elif self.action_code == 'UI_GO_TO_URL':
                            if ui_data == '':
                                raise ValueError('请提供要打开的URL地址')
                            self.run_result = ui_test.method.go_to_url(dr, ui_data)

                        # 刷新页面
                        elif self.action_code == 'UI_REFRESH':
                            dr.refresh()

                        # 前进
                        elif self.action_code == 'UI_FORWARD':
                            dr.forward()

                        # 后退
                        elif self.action_code == 'UI_BACK':
                            dr.back()

                        # 截图
                        elif self.action_code == 'UI_SCREENSHOT':
                            image = None
                            if self.ui_by != '' and ui_locator != '':
                                run_result_temp, visible_elements, _ = ui_test.method.wait_for_element_visible(
                                    dr=dr, by=self.ui_by, locator=ui_locator, timeout=self.timeout,
                                    base_element=ui_base_element, logger=self.logger)
                                if len(visible_elements) > 0:
                                    self.run_result, image = ui_test.screenshot.get_screenshot(dr, visible_elements[0])
                                else:
                                    self.run_result = ['f', '截图失败，原因为{}'.format(run_result_temp[1])]
                            else:
                                try:
                                    self.run_result, image = ui_test.screenshot.get_screenshot(dr)
                                except Exception as e:
                                    self.run_result = ['f', '截图失败，原因为{}'.format(getattr(e, 'msg', str(e)))]
                            if image:
                                self.img_list.append(image)

                        # 切换frame
                        elif self.action_code == 'UI_SWITCH_TO_FRAME':
                            self.run_result = ui_test.method.try_to_switch_to_frame(
                                dr=dr, by=self.ui_by, locator=ui_locator, timeout=self.timeout,
                                index_=self.ui_index, base_element=ui_base_element, logger=self.logger)

                        # 退出frame
                        elif self.action_code == 'UI_SWITCH_TO_DEFAULT_CONTENT':
                            dr.switch_to.default_content()

                        # 切换至浏览器的其他窗口或标签
                        elif self.action_code == 'UI_SWITCH_TO_WINDOW':
                            self.run_result, new_window_handle = ui_test.method.try_to_switch_to_window(
                                dr=dr, by=self.ui_by, locator=ui_locator, data=ui_data, timeout=self.timeout,
                                index_=self.ui_index, current_window_handle=dr.current_window_handle,
                                base_element=ui_base_element, logger=self.logger)

                        # 关闭当前浏览器窗口或标签并切换至其他窗口或标签
                        elif self.action_code == 'UI_CLOSE_WINDOW':
                            if len(dr.window_handles) < 2:
                                raise exceptions.InvalidSwitchToTargetException('当前窗口是浏览器的最后一个窗口，如果需要关闭浏览器请使用【重置浏览器】步骤')
                            current_window_handle = dr.current_window_handle
                            dr.close()
                            self.run_result, new_window_handle = ui_test.method.try_to_switch_to_window(
                                dr=dr, by=self.ui_by, locator=ui_locator, data=ui_data, timeout=self.timeout,
                                index_=self.ui_index, current_window_handle=current_window_handle,
                                base_element=ui_base_element, logger=self.logger)

                        # 重置浏览器
                        elif self.action_code == 'UI_RESET_BROWSER':
                            if dr is not None:
                                try:
                                    dr.quit()
                                except Exception as e:
                                    self.logger.error('有一个浏览器驱动无法关闭，请手动关闭。错误信息 => {}'.format(e))
                                del dr
                                init_timeout = self.timeout if self.timeout > 30 else 30
                                dr = ui_test.driver.get_driver(
                                    self.case_result.suite_result.suite.config, 3, init_timeout, logger=self.logger)
                                vic_case.driver_container[0] = dr

                        # 单击
                        elif self.action_code == 'UI_CLICK':
                            if self.ui_by == '' or ui_locator == '':
                                raise ValueError('无效的定位方式或定位符')
                            variable_elements = None
                            if self.ui_by == 'variable':
                                variable_elements = vic_variables.get_elements(
                                    ui_locator, vic_case.variables, global_variables)
                            elif self.ui_by == 'public element':
                                self.ui_by, ui_locator = ui_test.method.get_public_elements(
                                    ui_locator, public_elements)
                            self.run_result, self.elements = ui_test.method.try_to_click(
                                dr=dr, by=self.ui_by, locator=ui_locator, timeout=self.timeout,
                                index_=self.ui_index, base_element=ui_base_element,
                                variable_elements=variable_elements, logger=self.logger)
                            if self.save_as != '':
                                vic_case.variables.set_variable(self.save_as, self.elements)

                        # 输入
                        elif self.action_code == 'UI_ENTER':
                            if self.ui_by == '' or ui_locator == '':
                                raise ValueError('无效的定位方式或定位符')
                            variable_elements = None
                            if self.ui_by == 'variable':
                                variable_elements = vic_variables.get_elements(
                                    ui_locator, vic_case.variables, global_variables)
                            elif self.ui_by == 'public element':
                                self.ui_by, ui_locator = ui_test.method.get_public_elements(
                                    ui_locator, public_elements)
                            self.run_result, self.elements = ui_test.method.try_to_enter(
                                dr=dr, by=self.ui_by, locator=ui_locator, data=ui_data, timeout=self.timeout,
                                index_=self.ui_index, base_element=ui_base_element,
                                variable_elements=variable_elements, logger=self.logger)
                            if self.save_as != '':
                                vic_case.variables.set_variable(self.save_as, self.elements)

                        # 选择下拉项
                        elif self.action_code == 'UI_SELECT':
                            if self.ui_by == '' or ui_locator == '':
                                raise ValueError('无效的定位方式或定位符')
                            variable_elements = None
                            if self.ui_by == 'variable':
                                variable_elements = vic_variables.get_elements(
                                    ui_locator, vic_case.variables, global_variables)
                            elif self.ui_by == 'public element':
                                self.ui_by, ui_locator = ui_test.method.get_public_elements(
                                    ui_locator, public_elements)
                            self.run_result, self.elements = ui_test.method.try_to_select(
                                dr=dr, by=self.ui_by, locator=ui_locator, data=ui_data, timeout=self.timeout,
                                index_=self.ui_index, base_element=ui_base_element,
                                variable_elements=variable_elements, logger=self.logger)
                            if self.save_as != '':
                                vic_case.variables.set_variable(self.save_as, self.elements)

                        # 特殊动作
                        elif self.action_code == 'UI_SPECIAL_ACTION':
                            variable_elements = None
                            if self.ui_by == 'variable':
                                variable_elements = vic_variables.get_elements(
                                    ui_locator, vic_case.variables, global_variables)
                            elif self.ui_by == 'public element':
                                self.ui_by, ui_locator = ui_test.method.get_public_elements(
                                    ui_locator, public_elements)
                            self.run_result, self.elements = ui_test.method.perform_special_action(
                                dr=dr, by=self.ui_by, locator=ui_locator, data=ui_data, timeout=self.timeout,
                                index_=self.ui_index, special_action=self.ui_special_action,
                                base_element=ui_base_element, variables=vic_case.variables,
                                global_variables=global_variables, variable_elements=variable_elements,
                                logger=self.logger)

                            if self.save_as != '':
                                vic_case.variables.set_variable(self.save_as, self.elements)

                        # 移动到元素位置
                        elif self.action_code == 'UI_SCROLL_INTO_VIEW':
                            if self.ui_by == '' or ui_locator == '':
                                raise ValueError('无效的定位方式或定位符')
                            variable_elements = None
                            if self.ui_by == 'variable':
                                variable_elements = vic_variables.get_elements(
                                    ui_locator, vic_case.variables, global_variables)
                            elif self.ui_by == 'public element':
                                self.ui_by, ui_locator = ui_test.method.get_public_elements(
                                    ui_locator, public_elements)
                            self.run_result, self.elements = ui_test.method.try_to_scroll_into_view(
                                dr=dr, by=self.ui_by, locator=ui_locator, timeout=self.timeout,
                                index_=self.ui_index, base_element=ui_base_element,
                                variable_elements=variable_elements, logger=self.logger)
                            if self.save_as != '':
                                vic_case.variables.set_variable(self.save_as, self.elements)

                        # 验证URL
                        elif self.action_code == 'UI_VERIFY_URL':
                            if ui_data == '':
                                raise ValueError('无验证内容')
                            else:
                                self.run_result, new_url = ui_test.method.wait_for_page_redirect(
                                    dr=dr, new_url=ui_data, timeout=self.timeout, logger=self.logger)

                        # 验证文字
                        elif self.action_code == 'UI_VERIFY_TEXT':
                            if ui_data == '':
                                self.run_result = ['p', '无验证内容']
                                self.logger.info('【{}】\t未提供验证内容，跳过验证'.format(self.execute_id))
                            else:
                                if self.ui_by != 0 and ui_locator != '':
                                    variable_elements = None
                                    if self.ui_by == 'variable':
                                        variable_elements = vic_variables.get_elements(
                                            ui_locator, vic_case.variables, global_variables)
                                    elif self.ui_by == 'public element':
                                        self.ui_by, ui_locator = ui_test.method.get_public_elements(
                                            ui_locator, public_elements)
                                    self.run_result, self.elements, self.fail_elements \
                                        = ui_test.method.wait_for_text_present_with_locator(
                                            dr=dr, by=self.ui_by, locator=ui_locator, text=ui_data,
                                            timeout=self.timeout, index_=self.ui_index,
                                            base_element=ui_base_element, variable_elements=variable_elements,
                                            logger=self.logger)
                                else:
                                    self.run_result, self.elements = ui_test.method.wait_for_text_present(
                                        dr=dr, text=ui_data, timeout=self.timeout,
                                        base_element=ui_base_element, logger=self.logger
                                    )
                                if self.save_as != '':
                                    vic_case.variables.set_variable(self.save_as, self.elements)

                        # 验证元素可见
                        elif self.action_code == 'UI_VERIFY_ELEMENT_SHOW':
                            if self.ui_by == '' or ui_locator == '':
                                raise ValueError('无效的定位方式或定位符')
                            variable_elements = None
                            if self.ui_by == 'variable':
                                variable_elements = vic_variables.get_elements(
                                    ui_locator, vic_case.variables, global_variables)
                            elif self.ui_by == 'public element':
                                self.ui_by, ui_locator = ui_test.method.get_public_elements(
                                    ui_locator, public_elements)
                            if ui_data == '':
                                self.run_result, self.elements, elements_all = ui_test.method.wait_for_element_visible(
                                    dr=dr, by=self.ui_by, locator=ui_locator, timeout=self.timeout,
                                    base_element=ui_base_element, variable_elements=variable_elements,
                                    logger=self.logger)
                            else:
                                self.run_result, self.elements = ui_test.method.wait_for_element_visible_with_data(
                                    dr=dr, by=self.ui_by, locator=ui_locator, data=ui_data,
                                    timeout=self.timeout, base_element=ui_base_element,
                                    variable_elements=variable_elements, logger=self.logger)
                            if self.save_as != '':
                                vic_case.variables.set_variable(self.save_as, self.elements)

                        # 验证元素隐藏
                        elif self.action_code == 'UI_VERIFY_ELEMENT_HIDE':
                            if self.ui_by == '' or ui_locator == '':
                                raise ValueError('无效的定位方式或定位符')
                            variable_elements = None
                            if self.ui_by == 'variable':
                                variable_elements = vic_variables.get_elements(
                                    ui_locator, vic_case.variables, global_variables)
                            elif self.ui_by == 'public element':
                                self.ui_by, ui_locator = ui_test.method.get_public_elements(
                                    ui_locator, public_elements)
                            self.run_result, self.elements = ui_test.method.wait_for_element_disappear(
                                dr=dr, by=self.ui_by, locator=ui_locator, timeout=self.timeout,
                                base_element=ui_base_element, variable_elements=variable_elements,
                                logger=self.logger)
                            if self.save_as != '':
                                vic_case.variables.set_variable(self.save_as, self.elements)

                        # 运行JavaScript
                        elif self.action_code == 'UI_EXECUTE_JS':
                            if ui_data == '':
                                raise ValueError('未提供javascript代码')
                            variable_elements = None
                            if self.ui_by == 'variable':
                                variable_elements = vic_variables.get_elements(
                                    ui_locator, vic_case.variables, global_variables)
                            elif self.ui_by == 'public element':
                                self.ui_by, ui_locator = ui_test.method.get_public_elements(
                                    ui_locator, public_elements)
                            self.run_result, js_result = ui_test.method.run_js(
                                dr=dr, by=self.ui_by, locator=ui_locator, data=ui_data, timeout=self.timeout,
                                index_=self.ui_index, base_element=ui_base_element,
                                variable_elements=variable_elements, logger=self.logger)
                            if self.save_as != '':
                                msg = vic_case.variables.set_variable(self.save_as, js_result)
                                self.run_result[1] = '{}\n{}'.format(self.run_result[1], msg)

                        # 验证JavaScript结果
                        elif self.action_code == 'UI_VERIFY_JS_RETURN':
                            if ui_data == '':
                                raise ValueError('未提供javascript代码')
                            variable_elements = None
                            if self.ui_by == 'variable':
                                variable_elements = vic_variables.get_elements(
                                    ui_locator, vic_case.variables, global_variables)
                            elif self.ui_by == 'public element':
                                self.ui_by, ui_locator = ui_test.method.get_public_elements(
                                    ui_locator, public_elements)
                            self.run_result, js_result = ui_test.method.run_js(
                                dr=dr, by=self.ui_by, locator=ui_locator, data=ui_data, timeout=self.timeout,
                                index_=self.ui_index, base_element=ui_base_element,
                                variable_elements=variable_elements, logger=self.logger)
                            if js_result is not True:
                                self.run_result = ['f', self.run_result[1]]
                            if self.save_as != '':
                                msg = vic_case.variables.set_variable(self.save_as, js_result)
                                self.run_result[1] = '{}\n{}'.format(self.run_result[1], msg)

                        # 保存元素变量
                        elif self.action_code == 'UI_SAVE_ELEMENT':
                            if self.save_as == '':
                                raise ValueError('没有提供变量名')
                            if self.ui_by == '' or ui_locator == '':
                                raise ValueError('无效的定位方式或定位符')
                            variable_elements = None
                            if self.ui_by == 'variable':
                                variable_elements = vic_variables.get_elements(
                                    ui_locator, vic_case.variables, global_variables)
                            elif self.ui_by == 'public element':
                                self.ui_by, ui_locator = ui_test.method.get_public_elements(
                                    ui_locator, public_elements)
                            self.run_result, self.elements = ui_test.method.wait_for_element_present(
                                dr=dr, by=self.ui_by, locator=ui_locator, timeout=self.timeout,
                                base_element=ui_base_element, variable_elements=variable_elements,
                                logger=self.logger)

                            if self.run_result[0] == 'p':
                                msg = vic_case.variables.set_variable(self.save_as, self.elements)
                                self.run_result[1] = '{}\n{}'.format(self.run_result[1], msg)
                            else:
                                raise exceptions.NoSuchElementException('无法保存变量，{}'.format(self.run_result[1]))

                        # 保存url变量
                        elif self.action_code == 'UI_SAVE_URL':
                            if self.save_as == '':
                                raise ValueError('没有提供变量名')
                            self.run_result, data_ = ui_test.method.get_url(
                                dr=dr, condition_value=str(ui_data), logger=self.logger)

                            if self.run_result[0] == 'p':
                                msg = vic_case.variables.set_variable(self.save_as, data_)
                                self.run_result[1] = '{}\n{}'.format(self.run_result[1], msg)
                            else:
                                raise exceptions.WebDriverException('无法保存变量，{}'.format(self.run_result[1]))

                        # 保存元素文本
                        elif self.action_code == 'UI_SAVE_ELEMENT_TEXT':
                            if self.save_as == '':
                                raise ValueError('没有提供变量名')
                            if self.ui_by == '' or ui_locator == '':
                                raise ValueError('无效的定位方式或定位符')
                            variable_elements = None
                            if self.ui_by == 'variable':
                                variable_elements = vic_variables.get_elements(
                                    ui_locator, vic_case.variables, global_variables)
                            elif self.ui_by == 'public element':
                                self.ui_by, ui_locator = ui_test.method.get_public_elements(
                                    ui_locator, public_elements)
                            self.run_result, text = ui_test.method.get_element_text(
                                dr=dr, by=self.ui_by, locator=ui_locator, timeout=self.timeout,
                                index_=self.ui_index, base_element=ui_base_element,
                                variable_elements=variable_elements, logger=self.logger)

                            if self.run_result[0] == 'p':
                                msg = vic_case.variables.set_variable(self.save_as, text)
                                self.run_result[1] = '{}\n{}'.format(self.run_result[1], msg)
                            else:
                                raise exceptions.NoSuchElementException('无法保存变量，{}'.format(self.run_result[1]))

                        # 保存元素属性值
                        elif self.action_code == 'UI_SAVE_ELEMENT_ATTR':
                            if self.save_as == '':
                                raise ValueError('没有提供变量名')
                            if self.ui_by == '' or ui_locator == '':
                                raise ValueError('无效的定位方式或定位符')
                            variable_elements = None
                            if self.ui_by == 'variable':
                                variable_elements = vic_variables.get_elements(
                                    ui_locator, vic_case.variables, global_variables)
                            elif self.ui_by == 'public element':
                                self.ui_by, ui_locator = ui_test.method.get_public_elements(
                                    ui_locator, public_elements)
                            self.run_result, text = ui_test.method.get_element_attr(
                                dr=dr, by=self.ui_by, locator=ui_locator, data=ui_data, timeout=self.timeout,
                                index_=self.ui_index, base_element=ui_base_element,
                                variable_elements=variable_elements, logger=self.logger)

                            if self.run_result[0] == 'p':
                                msg = vic_case.variables.set_variable(self.save_as, text)
                                self.run_result[1] = '{}\n{}'.format(self.run_result[1], msg)
                            else:
                                raise exceptions.NoSuchAttributeException('无法保存变量，{}'.format(self.run_result[1]))

                        # ===== API =====
                        elif self.action_code == 'API_SEND_HTTP_REQUEST':
                            if not api_url:
                                raise ValueError('请提供请求地址')
                            response, response_body, _, _ = api_method.send_http_request(
                                api_url, method=self.api_method, headers=api_headers, body=api_body,
                                decode=api_decode, timeout=self.timeout, logger=self.logger)
                            try:
                                headers = json.loads(api_headers)
                                pretty_request_header = json.dumps(headers, indent=1, ensure_ascii=False)
                            except ValueError:
                                pretty_request_header = api_headers
                            pretty_response_header = json.dumps(response, indent=1, ensure_ascii=False)
                            run_result_status = 'p'

                            response_body_msg = response_body
                            if api_data:
                                run_result, response_body_msg = api_method.verify_http_response(
                                    api_data, response_body, self.logger)
                                if run_result[0] == 'p':
                                    prefix_msg = '请求发送完毕，结果验证通过'
                                else:
                                    run_result_status = 'f'
                                    prefix_msg = '请求发送完毕，结果验证失败'
                                suffix_msg = '验证结果：\n{}'.format(run_result[1])
                            else:
                                prefix_msg = '请求发送完毕'
                                suffix_msg = ''

                            if len(response_body_msg) > 10000:
                                response_body_msg = '{}\n*****（为节约空间，只保存了前10000个字符）*****'.format(
                                    response_body_msg[:10000])
                            msg = '{}\n请求地址：\n{}\n请求方式：\n{}\n请求头：\n{}\n请求体：\n{}\n响应状态：\n{} {}\n响应头：\n{}\n响应体：\n{}\n{}'.format(
                                prefix_msg, api_url, self.api_method, pretty_request_header, api_body,
                                response.status, response.reason, pretty_response_header, response_body_msg, suffix_msg)

                            if self.api_save and self.api_save != '[]':
                                try:
                                    api_save = json.loads(self.api_save)
                                except:
                                    self.logger.warning('【{}】\t待保存内容无法解析'.format(self.execute_id))
                                else:
                                    success, msg_ = api_method.save_http_response(
                                        response, response_body, api_save, vic_case.variables, logger=self.logger)
                                    msg = '{}\n变量保存：\n{}'.format(msg, msg_)
                                    if not success:
                                        run_result_status = 'f'
                            self.run_result = [run_result_status, msg]
                            self.logger.debug('【{}】\t{}'.format(self.execute_id, msg))

                        # ===== DB =====
                        elif self.action_code == 'DB_EXECUTE_SQL':
                            try:
                                row_count, sql_result = db_method.get_sql_result(
                                    db_type=self.db_type, db_host=db_host, db_port=db_port,
                                    db_name=db_name, db_user=db_user, db_password=db_password,
                                    db_lang=db_lang, sql=db_sql, timeout=timeout)
                            except:
                                self.logger.warning('【{}】\t连接数据库或SQL执行报错\nSQL语句：\n{}'.format(
                                    self.execute_id, db_sql), exc_info=True)
                                e_str = traceback.format_exc()
                                self.run_result = ['f', '连接数据库或SQL执行报错\nSQL语句：\n{}\n{}'.format(
                                    db_sql, e_str)]
                            else:
                                pretty_result = json.dumps(
                                    sql_result, indent=1, ensure_ascii=False, cls=db_method.JsonDatetimeEncoder)
                                if len(pretty_result) > 10000:
                                    pretty_result_ = '{}\n*****（为节约空间，只保存了前10000个字符）*****'.format(pretty_result[:10000])
                                else:
                                    pretty_result_ = pretty_result
                                self.logger.debug('【{}】\tSQL执行完毕\nSQL语句：\n{}\n{}\n结果集：\n{}'.format(
                                    self.execute_id, db_sql, row_count, pretty_result_))
                                if db_data:
                                    run_result = db_method.verify_sql_result(
                                        expect=db_data, sql_result=sql_result, logger=self.logger)
                                    if run_result[0] == 'p':
                                        self.run_result = [
                                            'p', 'SQL执行完毕，结果验证通过\nSQL语句：\n{}\n{}\n结果集：\n{}'.format(
                                                db_sql, row_count, pretty_result_)]
                                    else:
                                        self.run_result = [
                                            'f', 'SQL执行完毕，结果验证失败\nSQL语句：\n{}\n{}\n结果集：\n{}'.format(
                                                db_sql, row_count, pretty_result_)]
                                else:
                                    self.run_result = ['p', 'SQL执行完毕\nSQL语句：\n{}\n{}\n结果集：\n{}'.format(
                                        db_sql, row_count, pretty_result_)]

                        # ===== OTHER =====
                        # 等待
                        elif self.action_code == 'OTHER_SLEEP':
                            timeout = int(self.timeout or 3)
                            for i in range(timeout):
                                time.sleep(1)
                                self.logger.info('已等待【{}】秒'.format(i + 1))

                        # 保存用例变量
                        elif self.action_code == 'OTHER_SAVE_CASE_VARIABLE':
                            if self.save_as == '':
                                raise ValueError('没有提供变量名')
                            elif other_data == '':
                                raise ValueError('没有提供表达式')
                            else:
                                eo = vic_eval.EvalObject(
                                    other_data,
                                    vic_variables.get_variable_dict(vic_case.variables, global_variables), self.logger)
                                eval_success, eval_result, final_expression = eo.get_eval_result()
                                if eval_success:
                                    msg = vic_case.variables.set_variable(self.save_as, eval_result)
                                    self.run_result = ['p', '计算表达式：{}\n结果为：{}\n用例{}'.format(
                                        final_expression, eval_result, msg)]
                                else:
                                    raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))

                        # 保存全局变量
                        elif self.action_code == 'OTHER_SAVE_GLOBAL_VARIABLE':
                            if self.save_as == '':
                                raise ValueError('没有提供变量名')
                            elif other_data == '':
                                raise ValueError('没有提供表达式')
                            else:
                                eo = vic_eval.EvalObject(
                                    other_data,
                                    vic_variables.get_variable_dict(vic_case.variables, global_variables), self.logger)
                                eval_success, eval_result, final_expression = eo.get_eval_result()
                                if eval_success:
                                    msg = global_variables.set_variable(self.save_as, eval_result)
                                    self.run_result = ['p', '计算表达式：{}\n结果为：{}\n全局{}'.format(
                                        final_expression, eval_result, msg)]
                                else:
                                    raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))

                        # 转换变量类型
                        elif self.action_code == 'OTHER_CHANGE_VARIABLE_TYPE':
                            if other_data not in ('str', 'int', 'float', 'time', 'datetime'):
                                raise ValueError('无效的转换类型【{}】'.format(other_data))
                            found, variable = vic_variables.get_variable(
                                self.save_as, vic_case.variables, global_variables)
                            if not found:
                                raise ValueError('找不到名为【{}】的变量'.format(self.save_as))
                            try:
                                if other_data == 'str':
                                    variable = str(variable)
                                elif other_data == 'int':
                                    variable = int(variable)
                                elif other_data == 'float':
                                    variable = float(variable)
                                elif other_data == 'bool':
                                    variable = bool(variable)
                                elif other_data in ('time', 'datetime'):
                                    variable = vic_date_handle.str_to_time(str(variable))
                            except ValueError as e:
                                raise ValueError('变量类型转换失败，{}'.format(e))
                            if found == 'local':
                                vic_case.variables.set_variable(self.save_as, variable)
                            else:
                                global_variables.set_variable(self.save_as, variable)
                            self.run_result = ['p', '转换成功']

                        # 使用正则表达式截取变量
                        elif self.action_code == 'OTHER_GET_VALUE_WITH_RE':
                            if other_data == '':
                                raise ValueError('没有提供表达式')
                            found, variable = vic_variables.get_variable(
                                self.save_as, vic_case.variables, global_variables)
                            if not found:
                                raise ValueError('找不到名为【{}】的变量'.format(self.save_as))
                            find_result = vic_find_object.find_with_condition(
                                other_data, variable, logger=self.logger)
                            if find_result.is_matched and find_result.re_result:
                                variable = vic_find_object.get_first_str_in_re_result(find_result.re_result)
                                if found == 'local':
                                    vic_case.variables.set_variable(self.save_as, variable)
                                else:
                                    global_variables.set_variable(self.save_as, variable)
                                msg = '变量【{}】被截取为【{}】'.format(self.save_as, variable)
                                self.run_result = ['p', msg]
                            else:
                                msg = '无法匹配给定的正则表达式，所以变量【{}】的值没有改变'.format(self.save_as, variable)
                                self.run_result = ['f', msg]

                        # 验证表达式
                        elif self.action_code == 'OTHER_VERIFY_EXPRESSION':
                            if other_data == '':
                                raise ValueError('未提供表达式')
                            eo = vic_eval.EvalObject(
                                other_data, vic_variables.get_variable_dict(vic_case.variables, global_variables),
                                self.logger)
                            eval_success, eval_result, final_expression = eo.get_eval_result()
                            if eval_success:
                                if eval_result is True:
                                    self.run_result = ['p', '计算表达式：{}\n结果为：{}'.format(final_expression, eval_result)]
                                else:
                                    self.run_result = ['f', '计算表达式：{}\n结果为：{}'.format(final_expression, eval_result)]
                            else:
                                raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))

                        # 调用子用例
                        elif self.action_code == 'OTHER_CALL_SUB_CASE':
                            if self.other_sub_case is None:
                                raise ValueError('子用例为空或不存在')
                            elif self.other_sub_case.pk in vic_case.parent_case_pk_list:
                                raise RecursionError('子用例[ID:{}]【{}】被递归调用'.format(
                                    self.other_sub_case.pk, self.other_sub_case.name))
                            else:
                                from .vic_case import VicCase
                                sub_case = VicCase(
                                    case=self.other_sub_case,
                                    suite_result=self.case_result.suite_result,
                                    case_order=None,
                                    user=self.user,
                                    execute_str=self.execute_id,
                                    variables=vic_case.variables,
                                    step_result=self.step_result,
                                    parent_case_pk_list=vic_case.parent_case_pk_list,
                                    execute_uuid=self.execute_uuid,
                                    websocket_sender=self.websocket_sender,
                                    driver_container=vic_case.driver_container
                                )
                                sub_case_ = sub_case.execute(global_variables, public_elements)
                                case_result_ = sub_case_.case_result
                                # 更新driver
                                dr = vic_case.driver_container[0]
                                self.step_result.has_sub_case = True
                                if case_result_.error_count > 0 or case_result_.result_error:
                                    raise RuntimeError('子用例执行时出现错误')
                                elif case_result_.fail_count > 0:
                                    self.run_result = ['f', '子用例执行时验证失败']
                                elif case_result_.execute_count == 0:
                                    self.run_result = ['s', '子用例未执行']
                                else:
                                    self.run_result = ['p', '子用例执行成功']

                        # 无效的关键字
                        else:
                            raise exceptions.UnknownMethodException('未知的动作代码【{}】'.format(self.action_code))

                        if dr is not None:
                            try:
                                # 获取当前url
                                last_url = dr.current_url
                            except exceptions.UnexpectedAlertPresentException:  # 如有弹窗则处理弹窗
                                alert_handle_text, alert_text = ui_test.method.confirm_alert(
                                    dr=dr, alert_handle=self.ui_alert_handle, timeout=self.timeout, logger=self.logger)
                                self.logger.info(
                                    '【{}】\t处理了一个弹窗，处理方式为【{}】，弹窗内容为\n{}'.format(
                                        self.execute_id, alert_handle_text, alert_text))
                                last_url = dr.current_url

                            self.step_result.ui_last_url = last_url if last_url != 'data:,' else ''

                        # 获取UI验证截图
                        if self.action_code in (
                                'UI_VERIFY_URL', 'UI_VERIFY_TEXT', 'UI_VERIFY_ELEMENT_SHOW', 'UI_VERIFY_ELEMENT_HIDE'):
                            if self.ui_get_ss:
                                highlight_elements_map = {}
                                if len(self.elements) > 0:
                                    highlight_elements_map = ui_test.method.highlight(dr, self.elements, 'green')
                                if len(self.fail_elements) > 0:
                                    highlight_elements_map = {**highlight_elements_map,
                                                              **ui_test.method.highlight(dr, self.fail_elements, 'red')}
                                try:
                                    _, image = ui_test.screenshot.get_screenshot(dr)
                                    self.img_list.append(image)
                                except Exception:
                                    self.logger.warning('【{}】\t无法获取UI验证截图'.format(self.execute_id), exc_info=True)
                                if len(highlight_elements_map) > 0:
                                    ui_test.method.cancel_highlight(dr, highlight_elements_map)
                            else:
                                if len(self.elements) > 0:
                                    ui_test.method.highlight_for_a_moment(dr, self.elements, 'green')
                                if len(self.fail_elements) > 0:
                                    ui_test.method.highlight_for_a_moment(dr, self.fail_elements, 'red')
                    else:
                        self.run_result = ['s', '步骤被跳过']
                # 如果遇到元素过期，将尝试重跑该步骤，直到超时
                except (exceptions.StaleElementReferenceException, exceptions.WebDriverException) as e:
                    force_stop = FORCE_STOP.get(vic_case.execute_uuid)
                    if (force_stop and force_stop == self.user.pk) or (time.time() - start_time) > self.timeout:
                        raise
                    msg_ = 'element is not attached to the page document'
                    if isinstance(e, exceptions.StaleElementReferenceException) or msg_ in e.msg:
                        re_run = True
                        re_run_count += 1
                        self.logger.warning('【{}】\t元素已过期，可能是由于页面异步刷新导致，将尝试重新获取元素'.format(self.execute_id))
                    else:
                        raise

            if self.run_result[0] == 's':
                self.step_result.result_status = 0
            elif self.run_result[0] == 'p':
                self.step_result.result_status = 1
            else:
                self.step_result.result_status = 2
            self.step_result.result_message = self.run_result[1]

        except socket_timeout_error:
            self.socket_no_response = True
            self.logger.error('【{}】\t浏览器驱动响应超时'.format(self.execute_id), exc_info=True)
            self.step_result.result_status = 3
            self.step_result.result_message = '浏览器驱动响应超时，请检查网络连接或驱动位于的浏览器窗口是否被关闭'
            self.step_result.result_error = traceback.format_exc()
        except exceptions.TimeoutException:
            self.logger.error('【{}】\t超时'.format(self.execute_id), exc_info=True)
            self.step_result.result_status = 3
            self.step_result.result_message = '执行超时，请增大超时值'
            self.step_result.result_error = traceback.format_exc()
        except exceptions.InvalidSelectorException:
            self.logger.error('【{}】\t定位符【{}】无效'.format(self.execute_id, ui_locator), exc_info=True)
            self.step_result.result_status = 3
            self.step_result.result_message = '定位符【{}】无效'.format(ui_locator)
            self.step_result.result_error = traceback.format_exc()
        except Exception as e:
            self.logger.error('【{}】\t出错'.format(self.execute_id), exc_info=True)
            self.step_result.result_status = 3
            self.step_result.result_message = '执行出错：{}'.format(getattr(e, 'msg', str(e)))
            self.step_result.result_error = traceback.format_exc()

        if self.action_type_code == 'UI' and dr is not None:
            if self.socket_no_response:
                self.step_result.ui_last_url = '由于浏览器驱动响应超时，URL获取失败'
                self.logger.warning('【{}】\t由于浏览器驱动响应超时，无法获取报错时的URL和截图'.format(self.execute_id))

            # 获取当前URL
            try:
                last_url = dr.current_url
                self.step_result.ui_last_url = last_url if last_url != 'data:,' else ''
            except:
                self.logger.warning('【{}】\t无法获取报错时的URL'.format(self.execute_id))
                self.step_result.ui_last_url = 'URL获取失败'

            # 获取报错时截图
            if self.ui_get_ss and self.step_result.result_status == 3:
                try:
                    self.run_result, image = ui_test.screenshot.get_screenshot(dr)
                    self.img_list.append(image)
                except:
                    self.logger.warning('【{}】\t无法获取错误截图'.format(self.execute_id))

        # 关联截图
        for img in self.img_list:
            self.step_result.imgs.add(img)

        self.step_result.end_date = datetime.datetime.now()
        self.step_result.save()

        return self
