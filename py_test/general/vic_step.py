import datetime
import time
import json
import traceback
import uuid
from py_test.general import vic_variables, vic_public_elements, vic_log, vic_method
from py_test.ui_test import method
from selenium.common.exceptions import UnexpectedAlertPresentException, NoSuchElementException, TimeoutException, StaleElementReferenceException, WebDriverException
from py_test.vic_tools import vic_eval
from main.models import StepResult
from django.forms.models import model_to_dict

# 获取全局变量
global_variables = vic_variables.global_variables
# 获取公共元素组
public_elements = vic_public_elements.public_elements


class VicStep:
    def __init__(self, step, case_result, step_order, user, execute_str, variables, parent_case_pk_list, dr=None,
                 execute_uuid=uuid.uuid1(), websocket_sender=None):
        self.start_date = datetime.datetime.now()
        self.logger = vic_log.get_thread_logger(execute_uuid)

        self.step = step
        self.case_result = case_result
        self.user = user
        self.variables = variables
        self.dr = dr
        self.execute_uuid = execute_uuid
        self.websocket_sender = websocket_sender

        self.id = step.pk
        self.name = step.name
        self.action = step.action

        self.execute_id = '{}-{}'.format(execute_str, step_order)
        # 截图列表
        self.img_list = list()

        # 记录运行的case，防止递归调用
        if parent_case_pk_list is None:
            self.parent_case_pk_list = [case_result.case.pk]
        else:
            self.parent_case_pk_list = parent_case_pk_list
            self.parent_case_pk_list.append(case_result.case.pk)

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
            start_date=self.start_date,

            snapshot=json.dumps(model_to_dict(step)) if step else None,
        )

        try:
            self.run_result = ('p', '成功')
            self.elements = list()
            self.fail_elements = list()
            self.timeout = step.timeout if step.timeout else case_result.suite_result.timeout
            self.ui_get_ss = case_result.suite_result.ui_get_ss
            self.save_as = step.save_as
            ui_by_dict = {
                0: '',
                1: 'id',
                2: 'xpath',
                3: 'link text',
                4: 'partial link text',
                5: 'name',
                6: 'tag name',
                7: 'class name',
                8: 'css selector',
                9: 'public element',
                10: 'variable',
            }
            self.ui_by = ui_by_dict[step.ui_by]
            self.ui_locator = vic_method.replace_special_value(step.ui_locator, variables)
            self.ui_index = step.ui_index
            ui_base_element = vic_method.replace_special_value(step.ui_base_element, variables)
            self.ui_base_element = vic_variables.get_elements(ui_base_element, variables)[
                0] if ui_base_element != '' else None
            self.ui_data = vic_method.replace_special_value(step.ui_data, variables)
            ui_special_action_dict = {
                0: '',
                1: 'click',
                2: 'click_and_hold',
                3: 'context_click',
                4: 'double_click',
                5: 'release',
                6: 'move_by_offset',
                7: 'move_to_element',
                8: 'move_to_element_with_offset',
                9: 'drag_and_drop',
                10: 'drag_and_drop_by_offset',
                11: 'key_down',
                12: 'key_up',
                13: 'send_keys',
                14: 'send_keys_to_element',
            }
            self.ui_special_action = ui_special_action_dict[step.ui_special_action]
            ui_alert_handle_dict = {
                1: 'accept',
                2: 'dismiss',
                3: 'ignore',
            }
            self.ui_alert_handle = ui_alert_handle_dict.get(step.ui_alert_handle, 'accept')

            self.api_url = step.api_url
            self.api_headers = step.api_headers
            self.api_body = step.api_body
            self.api_data = step.api_data

            self.other_data = step.other_data
            self.other_sub_case = step.other_sub_case
        except Exception as e:
            self.logger.info('【{}】\t步骤读取出错'.format(self.execute_id), exc_info=True)
            self.step_result.result_status = 3
            self.step_result.result_message = '步骤读取出错：{}'.format(getattr(e, 'msg', str(e)))
            self.step_result.result_error = traceback.format_exc()
            raise

    def execute(self):
        # 保存result数据库对象
        self.step_result.save()
        dr = self.dr
        try:
            # ===== UI 初始化检查 =====
            if self.action.type.code == 'UI':
                if dr is None:
                    raise WebDriverException('浏览器未初始化，请检查是否配置有误或被关闭')
                # 设置selenium超时时间
                dr.implicitly_wait(self.timeout)
                dr.set_page_load_timeout(self.timeout)
                dr.set_script_timeout(self.timeout)
                # 设置driver超时时间
                dr.command_executor.set_timeout(self.timeout + 30)

            # 如果步骤执行过程中页面元素被改变导致出现StaleElementReferenceException，将自动再次执行步骤，直到超时
            start_time = time.time()
            re_run = True
            while (time.time() - start_time) <= self.timeout and re_run:
                re_run = False
                try:
                    # ===== UI =====
                    # 打开URL
                    if self.action.code == 'UI_GO_TO_URL':
                        if self.ui_data == '':
                            raise ValueError('请提供要打开的URL地址')
                        self.run_result = method.go_to_url(dr, self.ui_data)

                    # 刷新页面
                    elif self.action.code == 'UI_REFRESH':
                        dr.refresh()

                    # 前进
                    elif self.action.code == 'UI_FORWARD':
                        dr.forward()

                    # 后退
                    elif self.action.code == 'UI_BACK':
                        dr.back()

                    # 截图
                    elif self.action.code == 'UI_SCREENSHOT':
                        image = None
                        if self.ui_by != '' and self.ui_locator != '':
                            run_result_temp, visible_elements, _ = method.wait_for_element_visible(
                                dr=dr, by=self.ui_by, locator=self.ui_locator, timeout=self.timeout,
                                base_element=self.ui_base_element, logger=self.logger)
                            if len(visible_elements) > 0:
                                self.run_result, image = method.get_screenshot(dr, visible_elements[0])
                            else:
                                self.run_result = ('f', '截图失败，原因为{}'.format(run_result_temp[1]))
                        else:
                            self.run_result, image = method.get_screenshot(dr)
                        if image:
                            self.img_list.append(image)

                    # 切换frame
                    elif self.action.code == 'UI_SWITCH_TO_FRAME':
                        self.run_result = method.try_to_switch_to_frame(
                            dr=dr, by=self.ui_by, locator=self.ui_locator, index_=self.ui_index, timeout=self.timeout,
                            base_element=self.ui_base_element, logger=self.logger)

                    # 退出frame
                    elif self.action.code == 'UI_SWITCH_TO_DEFAULT_CONTENT':
                        dr.switch_to.default_content()

                    # 切换窗口
                    elif self.action.code == 'UI_SWITCH_TO_WINDOW':
                        self.run_result, new_window_handle = method.try_to_switch_to_window(
                            dr=dr, by=self.ui_by, locator=self.ui_locator, data=self.ui_data, timeout=self.timeout,
                            index_=self.ui_index, base_element=self.ui_base_element, logger=self.logger)

                    # 关闭窗口
                    elif self.action.code == 'UI_CLOSE_WINDOW':
                        dr.close()

                    # 重置浏览器
                    elif self.action.code == 'UI_RESET_BROWSER':
                        if dr is not None:
                            dr.quit()
                            dr = method.get_driver(
                                self.case_result.suite_result.suite.config, 3, self.timeout, logger=self.logger)

                    # 单击
                    elif self.action.code == 'UI_CLICK':
                        if self.ui_by == '' or self.ui_locator == '':
                            raise ValueError('无效的定位方式或定位符')
                        variable_elements = None
                        if self.ui_by == 'variable':
                            variable_elements = vic_variables.get_elements(self.ui_locator, self.variables)
                        elif self.ui_by == 'public element':
                            self.ui_by, self.ui_locator = method.get_public_elements(self.ui_locator, public_elements)
                        self.run_result, self.elements = method.try_to_click(
                            dr=dr, by=self.ui_by, locator=self.ui_locator, timeout=self.timeout, index_=self.ui_index,
                            base_element=self.ui_base_element, variable_elements=variable_elements, logger=self.logger)
                        if self.save_as != '':
                            self.variables.set_variable(self.save_as, self.elements)

                    # 输入
                    elif self.action.code == 'UI_ENTER':
                        if self.ui_by == '' or self.ui_locator == '':
                            raise ValueError('无效的定位方式或定位符')
                        variable_elements = None
                        if self.ui_by == 'variable':
                            variable_elements = vic_variables.get_elements(self.ui_locator, self.variables)
                        elif self.ui_by == 'public element':
                            self.ui_by, self.ui_locator = method.get_public_elements(self.ui_locator, public_elements)
                        self.run_result, self.elements = method.try_to_enter(
                            dr=dr, by=self.ui_by, locator=self.ui_locator, data=self.ui_data, timeout=self.timeout,
                            index_=self.ui_index, base_element=self.ui_base_element,
                            variable_elements=variable_elements, logger=self.logger)
                        if self.save_as != '':
                            self.variables.set_variable(self.save_as, self.elements)

                    # 选择下拉项
                    elif self.action.code == 'UI_SELECT':
                        if self.ui_by == '' or self.ui_locator == '':
                            raise ValueError('无效的定位方式或定位符')
                        variable_elements = None
                        if self.ui_by == 'variable':
                            variable_elements = vic_variables.get_elements(self.ui_locator, self.variables)
                        elif self.ui_by == 'public element':
                            self.ui_by, self.ui_locator = method.get_public_elements(self.ui_locator, public_elements)
                        self.run_result, self.elements = method.try_to_select(
                            dr=dr, by=self.ui_by, locator=self.ui_locator, data=self.ui_data, timeout=self.timeout,
                            index_=self.ui_index, base_element=self.ui_base_element,
                            variable_elements=variable_elements, logger=self.logger)
                        if self.save_as != '':
                            self.variables.set_variable(self.save_as, self.elements)

                    # 特殊动作
                    elif self.action.code == 'UI_SPECIAL_ACTION':
                        variable_elements = None
                        if self.ui_by == 'variable':
                            variable_elements = vic_variables.get_elements(self.ui_locator, self.variables)
                        elif self.ui_by == 'public element':
                            self.ui_by, self.ui_locator = method.get_public_elements(self.ui_locator, public_elements)
                        self.run_result, self.elements = method.perform_special_action(
                            dr=dr, by=self.ui_by, locator=self.ui_locator, data=self.ui_data, timeout=self.timeout,
                            index_=self.ui_index, base_element=self.ui_base_element,
                            special_action=self.ui_special_action, variables=self.variables,
                            variable_elements=variable_elements, logger=self.logger)

                        if self.save_as != '':
                            self.variables.set_variable(self.save_as, self.elements)

                    # 移动到元素位置
                    elif self.action.code == 'UI_SCROLL_INTO_VIEW':
                        if self.ui_by == '' or self.ui_locator == '':
                            raise ValueError('无效的定位方式或定位符')
                        variable_elements = None
                        if self.ui_by == 'variable':
                            variable_elements = vic_variables.get_elements(self.ui_locator, self.variables)
                        elif self.ui_by == 'public element':
                            self.ui_by, self.ui_locator = method.get_public_elements(self.ui_locator, public_elements)
                        self.run_result, self.elements = method.try_to_scroll_into_view(
                            dr=dr, by=self.ui_by, locator=self.ui_locator, timeout=self.timeout, index_=self.ui_index,
                            base_element=self.ui_base_element, variable_elements=variable_elements, logger=self.logger)
                        if self.save_as != '':
                            self.variables.set_variable(self.save_as, self.elements)

                    # 验证URL
                    elif self.action.code == 'UI_VERIFY_URL':
                        if self.ui_data == '':
                            raise ValueError('无验证内容')
                        else:
                            self.run_result, new_url = method.wait_for_page_redirect(
                                dr=dr, new_url=self.ui_data, timeout=self.timeout, logger=self.logger)

                    # 验证文字
                    elif self.action.code == 'UI_VERIFY_TEXT':
                        if self.ui_data == '':
                            self.run_result = ('p', '无验证内容')
                            self.logger.info('【{}】\t未提供验证内容，跳过验证'.format(self.execute_id))
                        else:
                            if self.ui_by != 0 and self.ui_locator != '':
                                variable_elements = None
                                if self.ui_by == 'variable':
                                    variable_elements = vic_variables.get_elements(self.ui_locator, self.variables)
                                elif self.ui_by == 'public element':
                                    self.ui_by, self.ui_locator = method.get_public_elements(
                                        self.ui_locator, public_elements)
                                self.run_result, self.elements, self.fail_elements \
                                    = method.wait_for_text_present_with_locator(
                                        dr=dr, by=self.ui_by, locator=self.ui_locator, text=self.ui_data,
                                        timeout=self.timeout, index_=self.ui_index,
                                        base_element=self.ui_base_element, variable_elements=variable_elements,
                                        logger=self.logger)
                            else:
                                self.run_result, self.elements = method.wait_for_text_present(
                                    dr=dr, text=self.ui_data, timeout=self.timeout, base_element=self.ui_base_element,
                                    logger=self.logger
                                )
                            if self.save_as != '':
                                self.variables.set_variable(self.save_as, self.elements)

                    # 验证元素可见
                    elif self.action.code == 'UI_VERIFY_ELEMENT_SHOW':
                        if self.ui_by == '' or self.ui_locator == '':
                            raise ValueError('无效的定位方式或定位符')
                        variable_elements = None
                        if self.ui_by == 'variable':
                            variable_elements = vic_variables.get_elements(self.ui_locator, self.variables)
                        elif self.ui_by == 'public element':
                            self.ui_by, self.ui_locator = method.get_public_elements(self.ui_locator, public_elements)
                        if self.ui_data == '':
                            self.run_result, self.elements, elements_all = method.wait_for_element_visible(
                                dr=dr, by=self.ui_by, locator=self.ui_locator, timeout=self.timeout,
                                base_element=self.ui_base_element, variable_elements=variable_elements,
                                logger=self.logger)
                        else:
                            self.run_result, self.elements = method.wait_for_element_visible_with_data(
                                dr=dr, by=self.ui_by, locator=self.ui_locator, data=self.ui_data, timeout=self.timeout,
                                base_element=self.ui_base_element, variable_elements=variable_elements,
                                logger=self.logger)
                        if self.save_as != '':
                            self.variables.set_variable(self.save_as, self.elements)

                    # 验证元素隐藏
                    elif self.action.code == 'UI_VERIFY_ELEMENT_HIDE':
                        if self.ui_by == '' or self.ui_locator == '':
                            raise ValueError('无效的定位方式或定位符')
                        variable_elements = None
                        if self.ui_by == 'variable':
                            variable_elements = vic_variables.get_elements(self.ui_locator, self.variables)
                        elif self.ui_by == 'public element':
                            self.ui_by, self.ui_locator = method.get_public_elements(self.ui_locator, public_elements)
                        self.run_result, self.elements = method.wait_for_element_disappear(
                            dr=dr, by=self.ui_by, locator=self.ui_locator, timeout=self.timeout,
                            base_element=self.ui_base_element, variable_elements=variable_elements, logger=self.logger)
                        if self.save_as != '':
                            self.variables.set_variable(self.save_as, self.elements)

                    # 运行JavaScript
                    elif self.action.code == 'UI_EXECUTE_JS':
                        if self.ui_data == '':
                            raise ValueError('未提供javascript代码')
                        variable_elements = None
                        if self.ui_by == 'variable':
                            variable_elements = vic_variables.get_elements(self.ui_locator, self.variables)
                        elif self.ui_by == 'public element':
                            self.ui_by, self.ui_locator = method.get_public_elements(self.ui_locator, public_elements)
                        self.run_result, js_result = method.run_js(
                            dr=dr, by=self.ui_by, locator=self.ui_locator, data=self.ui_data, timeout=self.timeout,
                            index_=self.ui_index, base_element=self.ui_base_element,
                            variable_elements=variable_elements, logger=self.logger)
                        if self.save_as != '':
                            self.variables.set_variable(self.save_as, js_result)

                    # 验证JavaScript结果
                    elif self.action.code == 'UI_VERIFY_JS_RETURN':
                        if self.ui_data == '':
                            raise ValueError('未提供javascript代码')
                        variable_elements = None
                        if self.ui_by == 'variable':
                            variable_elements = vic_variables.get_elements(self.ui_locator, self.variables)
                        elif self.ui_by == 'public element':
                            self.ui_by, self.ui_locator = method.get_public_elements(self.ui_locator, public_elements)
                        self.run_result, js_result = method.run_js(
                            dr=dr, by=self.ui_by, locator=self.ui_locator, data=self.ui_data, timeout=self.timeout,
                            index_=self.ui_index, base_element=self.ui_base_element,
                            variable_elements=variable_elements, logger=self.logger)
                        if js_result is not True:
                            self.run_result = ('f', self.run_result[1])
                        if self.save_as != '':
                            self.variables.set_variable(self.save_as, js_result)

                    # 保存元素变量
                    elif self.action.code == 'UI_SAVE_ELEMENT':
                        if self.save_as == '':
                            raise ValueError('没有提供变量名')
                        if self.ui_by == '' or self.ui_locator == '':
                            raise ValueError('无效的定位方式或定位符')
                        variable_elements = None
                        if self.ui_by == 'variable':
                            variable_elements = vic_variables.get_elements(self.ui_locator, self.variables)
                        elif self.ui_by == 'public element':
                            self.ui_by, self.ui_locator = method.get_public_elements(self.ui_locator, public_elements)
                        self.run_result, self.elements = method.wait_for_element_present(
                            dr=dr, by=self.ui_by, locator=self.ui_locator, timeout=self.timeout,
                            base_element=self.ui_base_element, variable_elements=variable_elements, logger=self.logger)
                        if self.run_result[0] == 'p':
                            self.variables.set_variable(self.save_as, self.elements)
                        else:
                            raise NoSuchElementException('无法保存变量，{}'.format(self.run_result[1]))

                    # ===== API =====
                    elif self.action.code == 0:
                        pass

                    # ===== DB =====
                    elif self.action.code == 0:
                        pass

                    # ===== OTHER =====
                    # 等待
                    elif self.action.code == 'OTHER_SLEEP':
                        if self.timeout == '':
                            time.sleep(5)
                        else:
                            time.sleep(self.timeout)

                    # 保存用例变量
                    elif self.action.code == 'OTHER_SAVE_CASE_VARIABLE':
                        if self.save_as == '':
                            raise ValueError('没有提供变量名')
                        elif self.other_data == '':
                            raise ValueError('没有提供表达式')
                        else:
                            eo = vic_eval.EvalObject(self.other_data, vic_variables.get_variable_dict(self.variables))
                            eval_success, eval_result, final_expression = eo.get_eval_result()
                            if eval_success:
                                self.variables.set_variable(self.save_as, eval_result)
                                self.run_result = (
                                    'p',
                                    '计算表达式：{}\n结果为：{}\n保存到局部变量【{}】'.format(
                                        final_expression, eval_result, self.save_as))

                            else:
                                raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))

                    # 保存全局变量
                    elif self.action.code == 'OTHER_SAVE_GLOBAL_VARIABLE':
                        if self.save_as == '':
                            raise ValueError('没有提供变量名')
                        elif self.other_data == '':
                            raise ValueError('没有提供表达式')
                        else:
                            eo = vic_eval.EvalObject(self.other_data, vic_variables.get_variable_dict(self.variables))
                            eval_success, eval_result, final_expression = eo.get_eval_result()
                            if eval_success:
                                global_variables.set_variable(self.save_as, eval_result)
                                self.run_result = (
                                    'p',
                                    '计算表达式：{}\n结果为：{}\n保存到全局变量【{}】'.format(
                                        final_expression, eval_result, self.save_as))
                            else:
                                raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))

                    # 验证表达式
                    elif self.action.code == 'OTHER_VERIFY_EXPRESSION':
                        if self.other_data == '':
                            raise ValueError('未提供表达式')
                        eo = vic_eval.EvalObject(self.other_data, vic_variables.get_variable_dict(self.variables))
                        eval_success, eval_result, final_expression = eo.get_eval_result()
                        if eval_success:
                            if eval_result is True:
                                self.run_result = ('p', '计算表达式：{}\n结果为：{}'.format(final_expression, eval_result))
                            else:
                                self.run_result = ('f', '计算表达式：{}\n结果为：{}'.format(final_expression, eval_result))
                        else:
                            raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))

                    # 调用子用例
                    elif self.action.code == 'OTHER_CALL_SUB_CASE':
                        if self.other_sub_case is None:
                            raise ValueError('子用例为空或不存在')
                        elif self.other_sub_case.pk in self.parent_case_pk_list:
                            raise ValueError('子用例[ID:{}]【{}】被递归调用'.format(
                                self.other_sub_case.pk, self.other_sub_case.name))
                        else:
                            from .vic_case import execute_case
                            case_result_ = execute_case(
                                case=self.other_sub_case,
                                suite_result=self.case_result.suite_result,
                                case_order=None,
                                user=self.user,
                                execute_str=self.execute_id,
                                variables=self.variables,
                                step_result=self.step_result,
                                parent_case_pk_list=self.parent_case_pk_list,
                                dr=dr,
                                execute_uuid=self.execute_uuid,
                                websocket_sender=self.websocket_sender)
                            self.step_result.has_sub_case = True
                            if case_result_.error_count > 0:
                                raise RuntimeError('子用例执行时出现错误')
                            elif case_result_.fail_count > 0:
                                self.run_result = ('f', '子用例执行时验证失败')
                            else:
                                self.run_result = ('p', '子用例执行成功')
                    # 无效的关键字
                    else:
                        raise ValueError('未知的action')

                    if dr is not None:
                        try:
                            # 获取当前url
                            last_url = dr.current_url
                        except UnexpectedAlertPresentException:  # 如有弹窗则处理弹窗
                            alert_handle_text, alert_text = method.confirm_alert(
                                dr=dr, alert_handle=self.ui_alert_handle, timeout=self.timeout, logger=self.logger)
                            self.logger.info(
                                '【{}】\t处理了一个弹窗，处理方式为【{}】，弹窗内容为\n{}'.format(
                                    self.execute_id, alert_handle_text, alert_text))
                            last_url = dr.current_url

                        self.step_result.ui_last_url = last_url if last_url != 'data:,' else ''

                    # 获取UI验证截图
                    if self.action.code in (
                            'UI_VERIFY_URL', 'UI_VERIFY_TEXT', 'UI_VERIFY_ELEMENT_SHOW', 'UI_VERIFY_ELEMENT_HIDE'):
                        if self.ui_get_ss:
                            highlight_elements_map = {}
                            if len(self.elements) > 0:
                                highlight_elements_map = method.highlight(dr, self.elements, 'green')
                            if len(self.fail_elements) > 0:
                                highlight_elements_map = {**highlight_elements_map,
                                                          **method.highlight(dr, self.fail_elements, 'red')}
                            try:
                                _, image = method.get_screenshot(dr)
                                self.img_list.append(image)
                            except Exception:
                                self.logger.info('【{}】\t无法获取UI验证截图'.format(self.execute_id), exc_info=True)
                            if len(highlight_elements_map) > 0:
                                method.cancel_highlight(dr, highlight_elements_map)
                        else:
                            if len(self.elements) > 0:
                                method.highlight_for_a_moment(dr, self.elements, 'green')
                            if len(self.fail_elements) > 0:
                                method.highlight_for_a_moment(dr, self.fail_elements, 'red')
                except StaleElementReferenceException:
                    re_run = True
                    self.logger.info('【{}】\t捕捉到元素过期异常，将尝试重新获取元素'.format(self.execute_id))

            if self.run_result[0] == 'p':
                self.step_result.result_status = 1
            else:
                self.step_result.result_status = 2
            self.step_result.result_message = self.run_result[1]

        except TimeoutException:
            self.logger.info('【{}】\t超时'.format(self.execute_id), exc_info=True)
            self.step_result.result_status = 3
            self.step_result.result_message = '执行超时，请增大超时值'
            self.step_result.result_error = traceback.format_exc()
        except Exception as e:
            self.logger.info('【{}】\t出错'.format(self.execute_id), exc_info=True)
            self.step_result.result_status = 3
            self.step_result.result_message = '执行出错：{}'.format(getattr(e, 'msg', str(e)))
            self.step_result.result_error = traceback.format_exc()

        # 获取报错时截图
        if dr is not None and self.ui_get_ss and self.action.type_id == 1 and self.step_result.result_status == 3:
            try:
                self.run_result, image = method.get_screenshot(dr)
                self.img_list.append(image)
            except Exception:
                self.logger.info('【{}】\t无法获取错误截图'.format(self.execute_id), exc_info=True)

        # 关联截图
        for img in self.img_list:
            self.step_result.imgs.add(img)

        self.step_result.end_date = datetime.datetime.now()
        self.step_result.save()
        return self.step_result


def debug(log_level=10):
    from main.models import Config, Step, CaseResult
    import logging
    from django.contrib.auth.models import User

    logger = logging.getLogger('py_test')
    logger.setLevel(log_level)
    # 设置线程日志level
    vic_log.THREAD_LEVEL = log_level

    config = Config.objects.get(pk=5)

    step = Step.objects.get(pk=5)
    case_result = CaseResult.objects.all()[0]

    step_order = 1
    user = User.objects.all()[0]
    execute_str = '<debug>'
    variables = vic_variables.Variables()
    parent_case_pk_list = None
    dr = method.get_driver(config)
    step = VicStep(step, case_result, step_order, user, execute_str, variables, parent_case_pk_list, dr)

    return step.execute()
