import datetime
import json
import traceback
import uuid
from py_test.general import vic_variables, vic_public_elements, vic_method, vic_log
from py_test.ui_test import method
from selenium.common.exceptions import UnexpectedAlertPresentException
from main.models import CaseResult, Step
from django.forms.models import model_to_dict
from .vic_step import VicStep
from utils.system import FORCE_STOP


class VicCase:
    def __init__(self, case, suite_result, case_order, user, execute_str, variables=None, step_result=None,
                 parent_case_pk_list=None, dr=None, execute_uuid=uuid.uuid1(), websocket_sender=None):
        self.start_date = datetime.datetime.now()
        self.logger = vic_log.get_thread_logger(execute_uuid)

        self.case = case
        self.suite_result = suite_result
        self.user = user
        self.execute_str = execute_str
        self.variables = variables
        self.step_result = step_result
        self.parent_case_pk_list = parent_case_pk_list
        self.dr = dr
        self.execute_uuid = execute_uuid
        self.websocket_sender = websocket_sender

        self.id = case.pk
        self.name = case.name
        self.steps = list()
        self.timeout = self.suite_result.timeout

        self.if_list = list()
        self.step_active = True

        # 初始化result数据库对象
        self.case_result = CaseResult(
            name=case.name,
            description=case.description,
            keyword=case.keyword,
            variable_group=json.dumps(model_to_dict(case.variable_group)) if case.variable_group else None,

            suite_result=suite_result,
            step_result=step_result,
            parent_case_pk_list=json.dumps(parent_case_pk_list) if parent_case_pk_list else None,
            case_order=case_order,
            case=case,
            creator=user,
            execute_count=0,
            pass_count=0,
            fail_count=0,
            error_count=0,
        )

    def execute(self):
        self.case_result.start_date = self.start_date
        # 保存result数据库对象
        self.case_result.save()

        # 用例初始化
        execute_id = '{}-{}'.format(self.execute_str, 0)
        try:
            self.logger.info('【{}】\t初始化 => {}'.format(execute_id, self.name))
            config = self.suite_result.suite.config
            # 初始化driver
            if self.step_result is None and config.ui_selenium_client != 0:
                self.dr = method.get_driver(config, 3, self.timeout, logger=self.logger)

            # 读取本地变量
            if self.variables is None:
                self.variables = vic_variables.Variables()
            local_variable_group = self.case.variable_group
            if local_variable_group is not None:
                for variable in local_variable_group.variable_set.all():
                    value = vic_method.replace_special_value(variable.value, self.variables)
                    self.variables.set_variable(variable.name, value)

            # 读取测试步骤数据
            steps = Step.objects.filter(case=self.case, is_active=True).order_by('casevsstep__order').select_related(
                'action')
            step_order = 0
            for step in steps:
                step_order += 1
                self.steps.append(
                    VicStep(
                        step=step, case_result=self.case_result, step_order=step_order, user=self.user,
                        execute_str=self.execute_str, variables=self.variables,
                        parent_case_pk_list=self.parent_case_pk_list, execute_uuid=self.execute_uuid,
                        websocket_sender=self.websocket_sender)
                )

        except Exception as e:
            self.logger.error('【{}】\t初始化出错'.format(execute_id), exc_info=True)
            self.case_result.result_message = '初始化出错：{}'.format(getattr(e, 'msg', str(e)))
            self.case_result.result_error = traceback.format_exc()

        ui_alert_handle = 'accept'  # 初始化弹窗处理方式
        step_order = 0

        for step in self.steps:
            # 强制停止
            force_stop = FORCE_STOP.get(self.execute_uuid)
            if force_stop and force_stop == self.user.pk:
                break

            step_order += 1
            execute_id = '{}-{}'.format(self.execute_str, step_order)
            self.logger.info('【{}】\t执行步骤 => ID:{} | {} | {}'.format(execute_id, step.id, step.name, step.step.action))

            timeout = step.timeout if not step.timeout else self.suite_result.suite.timeout

            # 如有弹窗则处理弹窗
            if self.dr is not None:
                try:
                    _ = self.dr.current_url
                except UnexpectedAlertPresentException:
                    alert_handle_text, alert_text = method.confirm_alert(
                        dr=self.dr, alert_handle=ui_alert_handle, timeout=timeout, logger=self.logger)
                    self.logger.info('【{}】\t处理了一个弹窗，处理方式为【{}】，弹窗内容为\n{}'.format(
                        execute_id, alert_handle_text, alert_text))

            # 执行步骤
            step_result_ = step.execute(self)

            # 获取最后一次弹窗处理方式
            ui_alert_handle = step.ui_alert_handle

            self.case_result.execute_count += 1
            if step_result_.result_status == 0:
                self.logger.info('【{}】\t跳过'.format(execute_id))
            elif step_result_.result_status == 1:
                self.case_result.pass_count += 1
                self.logger.info('【{}】\t执行成功'.format(execute_id))
            elif step_result_.result_status == 2:
                self.case_result.fail_count += 1
                self.logger.warning('【{}】\t执行失败'.format(execute_id))
            else:
                self.case_result.error_count += 1
                self.logger.error('【{}】\t执行出错，错误信息 => {}'.format(execute_id, step_result_.result_message))
                break

        if self.if_list:
            self.logger.warning('【{}】\t有{}个条件分支没有被关闭，可能会导致意外的错误，请添加结束标志以关闭分支'.format(self.execute_str, len(self.if_list)))

        # 如果不是子用例，且浏览器未关闭，且logging level大于等于10，则关闭浏览器
        if self.step_result is None and self.dr is not None and self.logger.level >= 10:
            try:
                self.dr.quit()
            except Exception as e:
                self.logger.error('有一个driver（浏览器）无法关闭，请手动关闭。错误信息 => {}'.format(e))
            del self.dr

        if self.case_result.error_count > 0 or self.case_result.result_error != '':
            self.case_result.result_status = 3
        elif self.case_result.fail_count > 0:
            self.case_result.result_status = 2
            self.case_result.result_message = '失败'
        else:
            self.case_result.result_status = 1
            self.case_result.result_message = '通过'
        self.case_result.end_date = datetime.datetime.now()
        self.case_result.save()
        # 关闭日志文件句柄
        for h in self.logger.handlers:
            h.close()
        return self.case_result
