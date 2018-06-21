import datetime
import time
import json
import traceback
import pytz
from py_test.general import vic_variables, vic_public_elements, thread_log
from py_test.ui_test import method
from selenium.common.exceptions import UnexpectedAlertPresentException, NoSuchElementException
from py_test.vic_tools import vic_eval
from py_test.vic_tools.vic_str_handle import change_digit_to_string, change_string_to_digit
from main.models import StepResult
from django.forms.models import model_to_dict

# 获取全局变量
global_variables = vic_variables.global_variables
# 获取公共元素组
public_elements = vic_public_elements.public_elements


def execute_step(step, case_result, step_order, user, execute_str, variables, parent_case_pk_list, dr=None):
    start_date = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    logger = thread_log.get_thread_logger()
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

        step_snapshot=json.dumps(model_to_dict(step)) if step else None,
    )
    try:
        step_action = step.action
        run_result = ('p', '成功')
        timeout = step.timeout if step.timeout else case_result.suite_result.base_timeout
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
        ui_locator = step.ui_locator
        ui_index = step.ui_index
        ui_base_element = step.ui_base_element
        ui_data = step.ui_data
        ui_special_action = step.ui_special_action
        ui_alert_handle = step.ui_alert_handle

        api_url = step.api_url
        api_headers = step.api_headers
        api_body = step.api_body
        api_data = step.api_data

        other_sub_case = step.other_sub_case

        # ===== UI =====
        # 打开URL
        if step_action.pk == 1:
            if ui_data == '':
                raise ValueError('请提供要打开的URL地址')
            run_result = method.go_to_url(dr, step.ui_data)

        # 刷新页面
        elif step_action.pk == 2:
            dr.refresh()

        # 前进
        elif step_action.pk == 3:
            dr.forward()

        # 后退
        elif step_action.pk == 4:
            dr.back()

        # 等待
        elif step_action.pk == 5:
            if ui_data == '':
                time.sleep(1)
            else:
                try:
                    second = change_string_to_digit(ui_data)
                except ValueError:
                    raise ValueError('无效的等待时间【{}】'.format(ui_data))
                time.sleep(second)

        # 截图
        elif step_action.pk == 6:
            if ui_by != '' and ui_locator != '':
                run_result_temp, visible_elements, _ = method.wait_for_element_visible(dr=dr, by=ui_by,
                                                                                       locator=ui_locator,
                                                                                       timeout=timeout,
                                                                                       base_element=ui_base_element)
                if len(visible_elements) > 0:
                    run_result, image_store = method.get_screenshot(dr, visible_elements[0])
                else:
                    run_result = ('f', '截图失败，原因为{}'.format(run_result_temp[1]))
            else:
                run_result, image_store = method.get_screenshot(dr)
            img_list.append(image_store)

        # 切换frame
        elif step_action.pk == 7:
            pass

        # 退出frame
        elif step_action.pk == 8:
            pass

        # 切换窗口
        elif step_action.pk == 9:
            pass

        # 关闭窗口
        elif step_action.pk == 10:
            pass

        # 重置浏览器
        elif step_action.pk == 11:
            if dr is not None:
                dr.quit()
                dr = method.get_driver(case_result.suite_result.suite.config)

        # 单击
        elif step_action.pk == 12:
            if ui_by == 0 or ui_locator == '':
                raise ValueError('无效的定位方式或定位符')
            variable_elements = None
            if ui_by == 10:
                variable_elements = vic_variables.get_elements(ui_locator, variables)
            elif ui_by == 9:
                ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
            run_result, elements = method.try_to_click(dr=dr, by=ui_by, locator=ui_locator, timeout=timeout,
                                                       index_=ui_index, base_element=ui_base_element,
                                                       variable_elements=variable_elements)
            if save_as != '':
                variables.set_variable(save_as, elements)

        # 双击
        elif step_action.pk == 13:
            pass

        # 输入
        elif step_action.pk == 14:
            if ui_by == 0 or ui_locator == '':
                raise ValueError('无效的定位方式或定位符')
            variable_elements = None
            if ui_by == 'variable':
                variable_elements = vic_variables.get_elements(ui_locator, variables)
            elif ui_by == 'public element':
                ui_by, ui_locator = method.get_public_elements(ui_locator, public_elements)
            run_result, elements = method.try_to_enter(dr=dr, by=ui_by, locator=ui_locator, data=ui_data,
                                                       timeout=timeout, index_=ui_index, base_element=ui_base_element,
                                                       variable_elements=variable_elements)
            if save_as != '':
                variables.set_variable(save_as, elements)

        # 特殊动作
        elif step_action.pk == 15:
            pass

        # 验证URL
        elif step_action.pk == 16:
            pass

        # 验证文字
        elif step_action.pk == 17:
            pass

        # 验证元素可见
        elif step_action.pk == 18:
            pass

        # ===== API =====
        elif step_action.pk == 0:
            pass

        # ===== DB =====
        elif step_action.pk == 0:
            pass

        # ===== OTHER =====
        # 调用子用例
        elif step_action.pk == 26:
            if step.other_sub_case is None:
                raise ValueError('子用例为空或不存在')
            elif step.other_sub_case.pk in parent_case_pk_list:
                raise ValueError('子用例【{} | {}】不允许递归调用'.format(step.other_sub_case.pk, step.other_sub_case.name))
            else:
                from .execute_case import execute_case
                case_result_ = execute_case(case=step.other_sub_case, suite_result=case_result.suite_result,
                                            case_order=None, user=user, execute_str=execute_id, variables=variables,
                                            step_result=step_result, parent_case_pk_list=parent_case_pk_list, dr=dr)
                if case_result_.error_count > 0:
                    raise RuntimeError('子用例运行中出现错误')
                elif case_result_.fail_count > 0:
                    run_result = ('f', '子用例中出现验证失败的步骤')
                else:
                    run_result = ('p', '子用例运行成功')
        else:
            raise ValueError('未知的action')
        if run_result[0] == 'p':
            step_result.result_status = 1
        else:
            step_result.result_status = 2
        step_result.result_message = run_result[1]
    except Exception as e:
        step_result.result_status = 3
        step_result.result_message = str(e)
        step_result.result_error = traceback.format_exc()
        logger.error('{}\t执行出错'.format(execute_id), exc_info=True)

    # 获取错误截图
    if step_result.result_status != 1 and step_action.type_id == 1 and dr is not None:
        try:
            run_result, image_store = method.get_screenshot(dr)
            img_list.append(image_store)
        except Exception:
            logger.warning('无法获取错误截图', exc_info=True)

    # 关联截图
    for img in img_list:
        step_result.imgs.add(img)

    step_result.end_date = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    step_result.save()
    return step_result


def debug(log_level=10):
    from main.models import Config, Step, CaseResult
    import logging
    from django.contrib.auth.models import User

    logger = logging.getLogger('py_test')
    logger.setLevel(log_level)
    # 设置线程日志level
    thread_log.THREAD_LEVEL = log_level

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
