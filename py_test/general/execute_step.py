import datetime
import time
import json
import traceback
import uuid
from py_test.general import vic_variables, vic_public_elements, vic_log, vic_method
from py_test.ui_test import method
from selenium.common.exceptions import UnexpectedAlertPresentException, NoSuchElementException, TimeoutException, WebDriverException
from py_test.vic_tools import vic_eval
from py_test.vic_tools.vic_str_handle import change_digit_to_string, change_string_to_digit
from main.models import StepResult
from django.forms.models import model_to_dict

# 获取全局变量
global_variables = vic_variables.global_variables
# 获取公共元素组
public_elements = vic_public_elements.public_elements


def execute_step(
        step, case_result, step_order, user, execute_str, variables, parent_case_pk_list, dr=None,
        execute_uuid=uuid.uuid1(), websocket_sender=None):

    start_date = datetime.datetime.now()
    logger = vic_log.get_thread_logger()

    execute_id = '{}-{}'.format(execute_str, step_order)
    # 截图列表
    img_list = list()

    # 记录运行的case，防止递归调用
    if parent_case_pk_list is None:
        parent_case_pk_list = [case_result.case.pk]
    else:
        parent_case_pk_list.append(case_result.case.pk)

    # 初始化case result
    step_result = StepResult.objects.create(
        name=step.name,
        description=step.description,
        keyword=step.keyword,
        action=step.action.full_name,

        case_result=case_result,
        step=step,
        step_order=step_order,
        creator=user,
        start_date=start_date,

        snapshot=json.dumps(model_to_dict(step)) if step else None,
    )

    try:
        step_action = step.action
        run_result = ('p', '成功')
        elements = list()
        fail_elements = list()
        timeout = step.timeout if step.timeout else case_result.suite_result.timeout
        ui_get_ss = case_result.suite_result.ui_get_ss
        save_as = step.save_as
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
        ui_by = ui_by_dict[step.ui_by]
        ui_locator = vic_method.replace_special_value(step.ui_locator, variables)
        ui_index = step.ui_index
        ui_base_element = vic_method.replace_special_value(step.ui_base_element, variables)
        ui_base_element = vic_variables.get_elements(ui_base_element, variables)[0] if ui_base_element != '' else None
        ui_data = vic_method.replace_special_value(step.ui_data, variables)
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
        ui_special_action = ui_special_action_dict[step.ui_special_action]
        ui_alert_handle_dict = {
            1: 'accept',
            2: 'dismiss',
            3: 'ignore',
        }
        ui_alert_handle = ui_alert_handle_dict.get(step.ui_alert_handle, 'accept')

        api_url = step.api_url
        api_headers = step.api_headers
        api_body = step.api_body
        api_data = step.api_data

        other_data = step.other_data
        other_sub_case = step.other_sub_case

        # ===== UI 初始化检查 =====
        if step_action.type.code == 'UI':
            if dr is None:
                raise WebDriverException('浏览器未初始化，请检查是否配置有误或被关闭')
            # 设置selenium超时时间
            dr.implicitly_wait(timeout)
            dr.set_page_load_timeout(timeout)
            dr.set_script_timeout(timeout)

        # ===== UI =====
        # 打开URL
        if step_action.code == 'UI_GO_TO_URL':
            if ui_data == '':
                raise ValueError('请提供要打开的URL地址')
            run_result = method.go_to_url(dr, ui_data)

        # 刷新页面
        elif step_action.code == 'UI_REFRESH':
            dr.refresh()

        # 前进
        elif step_action.code == 'UI_FORWARD':
            dr.forward()

        # 后退
        elif step_action.code == 'UI_BACK':
            dr.back()

        # 截图
        elif step_action.code == 'UI_SCREENSHOT':
            image = None
            if ui_by != '' and ui_locator != '':
                run_result_temp, visible_elements, _ = method.wait_for_element_visible(
                    dr=dr, by=ui_by, locator=ui_locator, timeout=timeout, base_element=ui_base_element)
                if len(visible_elements) > 0:
                    run_result, image = method.get_screenshot(dr, visible_elements[0])
                else:
                    run_result = ('f', '截图失败，原因为{}'.format(run_result_temp[1]))
            else:
                run_result, image = method.get_screenshot(dr)
            if image:
                img_list.append(image)

        # 切换frame
        elif step_action.code == 'UI_SWITCH_TO_FRAME':
            run_result = method.try_to_switch_to_frame(
                dr=dr, by=ui_by, locator=ui_locator, index_=ui_index, timeout=timeout, base_element=ui_base_element)

        # 退出frame
        elif step_action.code == 'UI_SWITCH_TO_DEFAULT_CONTENT':
            dr.switch_to.default_content()

        # 切换窗口
        elif step_action.code == 'UI_SWITCH_TO_WINDOW':
            run_result, new_window_handle = method.try_to_switch_to_window(
                dr=dr, by=ui_by, locator=ui_locator, data=ui_data, timeout=timeout, index_=ui_index,
                base_element=ui_base_element)

        # 关闭窗口
        elif step_action.code == 'UI_CLOSE_WINDOW':
            dr.close()

        # 重置浏览器
        elif step_action.code == 'UI_RESET_BROWSER':
            if dr is not None:
                dr.quit()
                dr = method.get_driver(case_result.suite_result.suite.config)

        # 单击
        elif step_action.code == 'UI_CLICK':
            if ui_by == '' or ui_locator == '':
                raise ValueError('无效的定位方式或定位符')
            variable_elements = None
            if ui_by == 10:
                variable_elements = vic_variables.get_elements(ui_locator, variables)
            elif ui_by == 9:
                ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
            run_result, elements = method.try_to_click(
                dr=dr, by=ui_by, locator=ui_locator, timeout=timeout, index_=ui_index, base_element=ui_base_element,
                variable_elements=variable_elements)
            if save_as != '':
                variables.set_variable(save_as, elements)

        # 输入
        elif step_action.code == 'UI_ENTER':
            if ui_by == '' or ui_locator == '':
                raise ValueError('无效的定位方式或定位符')
            variable_elements = None
            if ui_by == 'variable':
                variable_elements = vic_variables.get_elements(ui_locator, variables)
            elif ui_by == 'public element':
                ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
            run_result, elements = method.try_to_enter(
                dr=dr, by=ui_by, locator=ui_locator, data=ui_data, timeout=timeout, index_=ui_index,
                base_element=ui_base_element, variable_elements=variable_elements)
            if save_as != '':
                variables.set_variable(save_as, elements)

        # 选择下拉项
        elif step_action.code == 'UI_SELECT':
            if ui_by == '' or ui_locator == '':
                raise ValueError('无效的定位方式或定位符')
            variable_elements = None
            if ui_by == 'variable':
                variable_elements = vic_variables.get_elements(ui_locator, variables)
            elif ui_by == 'public element':
                ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
            run_result, elements = method.try_to_select(
                dr=dr, by=ui_by, locator=ui_locator, data=ui_data, timeout=timeout, index_=ui_index,
                base_element=ui_base_element, variable_elements=variable_elements)
            if save_as != '':
                variables.set_variable(save_as, elements)

        # 特殊动作
        elif step_action.code == 'UI_SPECIAL_ACTION':
            variable_elements = None
            if ui_by == 'variable':
                variable_elements = vic_variables.get_elements(ui_locator, variables)
            elif ui_by == 'public element':
                ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
            run_result, elements = method.perform_special_action(
                dr=dr, by=ui_by, locator=ui_locator, data=ui_data, timeout=timeout, index_=ui_index,
                base_element=ui_base_element, special_action=ui_special_action, variables=variables,
                variable_elements=variable_elements)

            if save_as != '':
                variables.set_variable(save_as, elements)

        # 移动到元素位置
        elif step_action.code == 'UI_SCROLL_INTO_VIEW':
            if ui_by == '' or ui_locator == '':
                raise ValueError('无效的定位方式或定位符')
            variable_elements = None
            if ui_by == 'variable':
                variable_elements = vic_variables.get_elements(ui_locator, variables)
            elif ui_by == 'public element':
                ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
            run_result, elements = method.try_to_scroll_into_view(
                dr=dr, by=ui_by, locator=ui_locator, timeout=timeout, index_=ui_index,
                base_element=ui_base_element, variable_elements=variable_elements)
            if save_as != '':
                variables.set_variable(save_as, elements)

        # 验证URL
        elif step_action.code == 'UI_VERIFY_URL':
            if ui_data == '':
                raise ValueError('无验证内容')
            else:
                run_result, new_url = method.wait_for_page_redirect(dr=dr, new_url=ui_data, timeout=timeout)

        # 验证文字
        elif step_action.code == 'UI_VERIFY_TEXT':
            if ui_data == '':
                run_result = ('p', '无验证内容')
                logger.warning('【{}】\t未提供验证内容，跳过验证'.format(execute_id))
            else:
                if ui_by != 0 and ui_locator != '':
                    variable_elements = None
                    if ui_by == 'variable':
                        variable_elements = vic_variables.get_elements(ui_locator, variables)
                    elif ui_by == 'public element':
                        ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
                    run_result, elements, fail_elements = method.wait_for_text_present_with_locator(
                        dr=dr, by=ui_by, locator=ui_locator, text=ui_data, timeout=timeout, index_=ui_index,
                        base_element=ui_base_element, variable_elements=variable_elements)
                else:
                    run_result, elements = method.wait_for_text_present(
                        dr=dr, text=ui_data, timeout=timeout, base_element=ui_base_element)
                if save_as != '':
                    variables.set_variable(save_as, elements)

        # 验证元素可见
        elif step_action.code == 'UI_VERIFY_ELEMENT_SHOW':
            if ui_by == '' or ui_locator == '':
                raise ValueError('无效的定位方式或定位符')
            variable_elements = None
            if ui_by == 'variable':
                variable_elements = vic_variables.get_elements(ui_locator, variables)
            elif ui_by == 'public element':
                ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
            if ui_data == '':
                run_result, elements, elements_all = method.wait_for_element_visible(
                    dr=dr, by=ui_by, locator=ui_locator, timeout=timeout, base_element=ui_base_element,
                    variable_elements=variable_elements)
            else:
                run_result, elements = method.wait_for_element_visible_with_data(
                    dr=dr, by=ui_by, locator=ui_locator, data=ui_data, timeout=timeout, base_element=ui_base_element,
                    variable_elements=variable_elements)
            if save_as != '':
                variables.set_variable(save_as, elements)

        # 验证元素隐藏
        elif step_action.code == 'UI_VERIFY_ELEMENT_HIDE':
            if ui_by == '' or ui_locator == '':
                raise ValueError('无效的定位方式或定位符')
            variable_elements = None
            if ui_by == 'variable':
                variable_elements = vic_variables.get_elements(ui_locator, variables)
            elif ui_by == 'public element':
                ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
            run_result, elements = method.wait_for_element_disappear(
                dr=dr, by=ui_by, locator=ui_locator, timeout=timeout, base_element=ui_base_element,
                variable_elements=variable_elements)
            if save_as != '':
                variables.set_variable(save_as, elements)

        # 运行JavaScript
        elif step_action.code == 'UI_EXECUTE_JS':
            if ui_data == '':
                raise ValueError('未提供javascript代码')
            variable_elements = None
            if ui_by == 'variable':
                variable_elements = vic_variables.get_elements(ui_locator, variables)
            elif ui_by == 'public element':
                ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
            run_result, js_result = method.run_js(
                dr=dr, by=ui_by, locator=ui_locator, data=ui_data, timeout=timeout, index_=ui_index,
                base_element=ui_base_element, variable_elements=variable_elements)
            if save_as != '':
                variables.set_variable(save_as, js_result)

        # 验证JavaScript结果
        elif step_action.code == 'UI_VERIFY_JS_RETURN':
            if ui_data == '':
                raise ValueError('未提供javascript代码')
            variable_elements = None
            if ui_by == 'variable':
                variable_elements = vic_variables.get_elements(ui_locator, variables)
            elif ui_by == 'public element':
                ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
            run_result, js_result = method.run_js(
                dr=dr, by=ui_by, locator=ui_locator, data=ui_data, timeout=timeout, index_=ui_index,
                base_element=ui_base_element, variable_elements=variable_elements)
            if js_result is not True:
                run_result = ('f', run_result[1])
            if save_as != '':
                variables.set_variable(save_as, js_result)

        # 保存元素变量
        elif step_action.code == 'UI_SAVE_ELEMENT':
            if save_as == '':
                raise ValueError('没有提供变量名')
            if ui_by == '' or ui_locator == '':
                raise ValueError('无效的定位方式或定位符')
            variable_elements = None
            if ui_by == 'variable':
                variable_elements = vic_variables.get_elements(ui_locator, variables)
            elif ui_by == 'public element':
                ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
            run_result, elements = method.wait_for_element_present(
                dr=dr, by=ui_by, locator=ui_locator, timeout=timeout, base_element=ui_base_element,
                variable_elements=variable_elements)
            if run_result[0] == 'p':
                variables.set_variable(save_as, elements)
            else:
                raise NoSuchElementException('无法保存变量，{}'.format(run_result[1]))

        # ===== API =====
        elif step_action.code == 0:
            pass

        # ===== DB =====
        elif step_action.code == 0:
            pass

        # ===== OTHER =====
        # 等待
        elif step_action.code == 'OTHER_SLEEP':
            if timeout == '':
                time.sleep(5)
            else:
                time.sleep(timeout)

        # 保存用例变量
        elif step_action.code == 'OTHER_SAVE_CASE_VARIABLE':
            if save_as == '':
                raise ValueError('没有提供变量名')
            elif other_data == '':
                raise ValueError('没有提供表达式')
            else:
                eo = vic_eval.EvalObject(other_data, vic_variables.get_variable_dict(variables))
                eval_success, eval_result, final_expression = eo.get_eval_result()
                if eval_success:
                    variables.set_variable(save_as, eval_result)
                    run_result = (
                        'p', '计算表达式：{}\n结果为：{}\n保存到局部变量【{}】'.format(final_expression, eval_result, save_as))

                else:
                    raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))

        # 保存全局变量
        elif step_action.code == 'OTHER_SAVE_GLOBAL_VARIABLE':
            if save_as == '':
                raise ValueError('没有提供变量名')
            elif other_data == '':
                raise ValueError('没有提供表达式')
            else:
                eo = vic_eval.EvalObject(other_data, vic_variables.get_variable_dict(variables))
                eval_success, eval_result, final_expression = eo.get_eval_result()
                if eval_success:
                    global_variables.set_variable(save_as, eval_result)
                    run_result = (
                        'p', '计算表达式：{}\n结果为：{}\n保存到全局变量【{}】'.format(final_expression, eval_result, save_as))
                else:
                    raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))

        # 验证表达式
        elif step_action.code == 'OTHER_VERIFY_EXPRESSION':
            if other_data == '':
                raise ValueError('未提供表达式')
            eo = vic_eval.EvalObject(other_data, vic_variables.get_variable_dict(variables))
            eval_success, eval_result, final_expression = eo.get_eval_result()
            if eval_success:
                if eval_result is True:
                    run_result = ('p', '计算表达式：{}\n结果为：{}'.format(final_expression, eval_result))
                else:
                    run_result = ('f', '计算表达式：{}\n结果为：{}'.format(final_expression, eval_result))
            else:
                raise ValueError('不合法的表达式：{}\n错误信息：{}'.format(final_expression, eval_result))

        # 调用子用例
        elif step_action.code == 'OTHER_CALL_SUB_CASE':
            if other_sub_case is None:
                raise ValueError('子用例为空或不存在')
            elif other_sub_case.pk in parent_case_pk_list:
                raise ValueError('子用例[ID:{}]【{}】被递归调用'.format(other_sub_case.pk, other_sub_case.name))
            else:
                from .execute_case import execute_case
                case_result_ = execute_case(case=other_sub_case, suite_result=case_result.suite_result, case_order=None,
                                            user=user, execute_str=execute_id, variables=variables,
                                            step_result=step_result, parent_case_pk_list=parent_case_pk_list, dr=dr,
                                            execute_uuid=execute_uuid, websocket_sender=websocket_sender)
                step_result.has_sub_case = True
                if case_result_.error_count > 0:
                    raise RuntimeError('子用例执行时出现错误')
                elif case_result_.fail_count > 0:
                    run_result = ('f', '子用例执行时验证失败')
                else:
                    run_result = ('p', '子用例执行成功')
        # 无效的关键字
        else:
            raise ValueError('未知的action')

        if dr is not None:
            try:
                # 获取当前url
                last_url = dr.current_url
            except UnexpectedAlertPresentException:  # 如有弹窗则处理弹窗
                alert_handle_text, alert_text = method.confirm_alert(
                    dr=dr, alert_handle=ui_alert_handle, timeout=timeout)
                logger.info(
                    '【{}】\t处理了一个弹窗，处理方式为【{}】，弹窗内容为\n{}'.format(execute_id, alert_handle_text, alert_text))
                last_url = dr.current_url

            step_result.ui_last_url = last_url if last_url != 'data:,' else ''

        # 获取UI验证截图
        if step_action.code in ('UI_VERIFY_URL', 'UI_VERIFY_TEXT', 'UI_VERIFY_ELEMENT_SHOW', 'UI_VERIFY_ELEMENT_HIDE'):
            if ui_get_ss:
                highlight_elements_map = {}
                if len(elements) > 0:
                    highlight_elements_map = method.highlight(dr, elements, 'green')
                if len(fail_elements) > 0:
                    highlight_elements_map = {**highlight_elements_map,
                                              **method.highlight(dr, fail_elements, 'red')}
                try:
                    _, image = method.get_screenshot(dr)
                    img_list.append(image)
                except Exception:
                    logger.warning('【{}】\t无法获取UI验证截图'.format(execute_id), exc_info=True)
                if len(highlight_elements_map) > 0:
                    method.cancel_highlight(dr, highlight_elements_map)
            else:
                if len(elements) > 0:
                    method.highlight_for_a_moment(dr, elements, 'green')
                if len(fail_elements) > 0:
                    method.highlight_for_a_moment(dr, fail_elements, 'red')

        if run_result[0] == 'p':
            step_result.result_status = 1
        else:
            step_result.result_status = 2
        step_result.result_message = run_result[1]
    except TimeoutException:
        logger.error('【{}】\t执行超时'.format(execute_id), exc_info=True)
        step_result.result_status = 3
        step_result.result_message = '执行超时，请增大超时值'
        step_result.result_error = traceback.format_exc()
    except Exception as e:
        logger.error('【{}】\t执行出错'.format(execute_id), exc_info=True)
        step_result.result_status = 3
        step_result.result_message = '执行出错：{}'.format(getattr(e, 'msg', str(e)))
        step_result.result_error = traceback.format_exc()

        # 获取报错时截图
        if dr is not None and ui_get_ss and step_action.type_id == 1:
            try:
                run_result, image = method.get_screenshot(dr)
                img_list.append(image)
            except Exception:
                logger.warning('【{}】\t无法获取错误截图'.format(execute_id), exc_info=True)

    # 关联截图
    for img in img_list:
        step_result.imgs.add(img)

    step_result.end_date = datetime.datetime.now()
    step_result.save()
    return step_result


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

    return execute_step(step, case_result, step_order, user, execute_str, variables, parent_case_pk_list, dr)
