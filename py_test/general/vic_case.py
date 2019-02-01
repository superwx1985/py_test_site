import datetime
import json
import traceback
from py_test.general import vic_variables, vic_method
from py_test import ui_test
from selenium.common.exceptions import UnexpectedAlertPresentException
from main.models import CaseResult, Step
from django.forms.models import model_to_dict
from .public_items import status_str_dict
from .vic_step import VicStep
from utils.other import check_recursive_call


class VicCase:
    def __init__(
            self, case, case_order, vic_suite, execute_str, variables=None, vic_step=None, parent_case_pk_list=None,
            driver_container=None):
        self.logger = vic_suite.logger

        self.case = case
        self.case_order = case_order
        self.vic_suite = vic_suite
        self.name = case.name
        self.user = vic_suite.user
        self.execute_uuid = vic_suite.execute_uuid
        self.status = 0
        self.init_date = datetime.datetime.now()
        self.start_date = None
        self.end_date = None

        self.execute_str = execute_str

        self.variables = variables
        self.global_variables = vic_suite.global_variables
        self.public_elements = vic_suite.public_elements
        self.vic_step = vic_step

        # 记录用例id以防递归调用
        if not parent_case_pk_list:
            parent_case_pk_list = list()
        parent_case_pk_list.append(case.pk)
        self.parent_case_pk_list = parent_case_pk_list

        self.name = case.name
        self.steps = list()

        # timeout为0时也要取
        self.timeout = case.timeout if case.timeout is not None else vic_suite.timeout
        # ui_step_interval为0时也要取
        self.ui_step_interval = case.ui_step_interval if case.ui_step_interval is not None \
            else vic_suite.ui_step_interval

        self.force_stop_ = False  # 强制停止信号

        # 分支列表
        self.if_list = list()
        # 步骤激活标志
        self.step_active = True

        # 循环列表
        self.loop_list = list()
        # 循环迭代次数
        self.loop_active = False

        self.config = self.vic_suite.config

        # 获取变量组json
        variable_group_json = None
        if case.variable_group and case.variable_group.is_active:
            v_list = list(case.variable_group.variable_set.all().values('pk', 'name', 'description', 'value', 'order'))
            variable_group_dict = model_to_dict(case.variable_group)
            variable_group_dict['variables'] = v_list
            variable_group_json = json.dumps(variable_group_dict)

        # 驱动停止响应标志
        self.socket_no_response = False

        # 初始化result数据库对象
        self.case_result = CaseResult.objects.create(
            name=case.name,
            description=case.description,
            keyword=case.keyword,

            timeout=case.timeout,
            ui_step_interval=case.ui_step_interval,
            variable_group=variable_group_json,

            suite_result=vic_suite.suite_result,
            step_result=vic_step.step_result if vic_step else None,
            parent_case_pk_list=json.dumps(parent_case_pk_list) if parent_case_pk_list else None,
            case_order=case_order,
            case=case,
            creator=self.user,
            execute_count=0,
            pass_count=0,
            fail_count=0,
            error_count=0,
        )

        # driver容器，用于在运行过程中更换driver
        self.driver_container = driver_container or [None]

    # 强制停止标志
    @property
    def force_stop(self):
        if self.force_stop_ or self.vic_suite.force_stop or (self.vic_step.force_stop if self.vic_step else False):
            self.force_stop_ = True
            self.status = 2
            return True
        else:
            return False

    @property
    def status_str(self):
        return status_str_dict[self.status]

    def execute(self):
        # 记录开始执行时的时间
        self.start_date = self.case_result.start_date = datetime.datetime.now()
        self.status = 1

        execute_id = self.execute_str
        
        # 从容器中获取driver
        dr = self.driver_container[0]

        if not self.force_stop:
            # 用例初始化
            execute_id = '{}-{}'.format(self.execute_str, 0)
            try:
                self.logger.info('【{}】\t初始化 => {}'.format(execute_id, self.name))

                # 判断是否递归调用
                recursive_id, case_list = check_recursive_call(self.case)
                if recursive_id:
                    raise RecursionError('用例[ID:{}]被用例[ID:{}]递归调用，执行中止。调用顺序列表：{}'.format(
                            recursive_id, case_list[-1], case_list))

                # 初始化driver
                if not dr and not self.vic_step and self.config.ui_selenium_client != 0:
                    init_timeout = self.timeout if self.timeout > 30 else 30
                    self.logger.info('【{}】\t启动浏览器...'.format(execute_id))
                    dr = ui_test.driver.get_driver(self.config, 3, init_timeout, logger=self.logger)
                    self.driver_container[0] = dr

                # 读取本地变量
                if self.variables is None:
                    self.variables = vic_variables.Variables(self.logger)
                local_variable_group = self.case.variable_group
                if local_variable_group and local_variable_group.is_active:
                    for variable in local_variable_group.variable_set.all():
                        value = vic_method.replace_special_value(
                            variable.value, self.variables, self.global_variables, self.logger)
                        self.variables.set_variable(variable.name, value)

                # 读取测试步骤数据
                steps = Step.objects.filter(case=self.case, is_active=True).order_by(
                    'casevsstep__order').select_related('action', 'action__type')
                step_order = 0
                for step in steps:
                    step_order += 1
                    self.steps.append(VicStep(step=step, vic_case=self, step_order=step_order))

            except Exception as e:
                self.logger.error('【{}】\t初始化出错'.format(execute_id), exc_info=True)
                self.case_result.result_message = '初始化出错：{}'.format(getattr(e, 'msg', str(e)))
                self.case_result.result_error = traceback.format_exc()

            # 执行步骤
            try:
                step_index = 0
                while step_index < len(self.steps):

                    if self.force_stop:
                        break

                    step = self.steps[step_index]
                    step_index += 1
                    execute_id = '{}-{}'.format(self.execute_str, step_index)

                    # 如果处于循环体
                    if self.loop_list:
                        loop_id = ''
                        is_first = True
                        for loop_ in self.loop_list:
                            loop_id = '{}({})'.format(loop_id, loop_[1])
                            if loop_[1] > 1:
                                is_first = False
                        execute_id = '{}{}'.format(execute_id, loop_id)
                        # 如果不是首次迭代，获取新的vic step对象
                        if not is_first:
                            _step = step.step
                            _step_order = step.step_order
                            step = VicStep(step=_step, vic_case=self, step_order=_step_order)
                        step.execute_id = execute_id
                        step.loop_id = loop_id

                    self.logger.info('【{}】\t执行步骤 => ID:{} | {} | {}'.format(
                        execute_id, step.id, step.name, step.step.action))

                    # 执行步骤
                    step_ = step.execute()
                    step_result_ = step_.step_result
                    self.socket_no_response = step_.socket_no_response

                    # 更新driver
                    dr = self.driver_container[0]

                    self.case_result.execute_count += 1
                    if step_result_.result_state == 0:
                        self.logger.info('【{}】\t跳过'.format(execute_id))
                    elif step_result_.result_state == 1:
                        self.case_result.pass_count += 1
                        self.logger.info('【{}】\t执行成功'.format(execute_id))
                    elif step_result_.result_state == 2:
                        self.case_result.fail_count += 1
                        self.logger.warning('【{}】\t执行失败'.format(execute_id))
                    elif step_result_.result_state == 3:
                        self.case_result.error_count += 1
                        self.logger.error('【{}】\t执行出错，错误信息 => {}'.format(execute_id, step_result_.result_message))
                        break

                    # 处理循环标志
                    if self.loop_active:
                        step_index = self.loop_list[-1][0] + 1
                        self.loop_active = False

            except Exception as e:
                self.logger.error('【{}】\t执行出错'.format(execute_id), exc_info=True)
                self.case_result.result_message = '执行出错：{}'.format(getattr(e, 'msg', str(e)))
                self.case_result.result_error = traceback.format_exc()

        if self.if_list:
            self.logger.warning('【{}】\t有{}个条件分支块缺少关闭步骤，可能会导致意外的错误，请添加关闭步骤'.format(
                execute_id, len(self.if_list)))
        if self.loop_list:
            self.logger.warning('【{}】\t有{}个循环块缺少关闭步骤，可能会导致意外的错误，请添加关闭步骤'.format(
                execute_id, len(self.loop_list)))

        # 如果不是子用例，且浏览器未关闭，则关闭浏览器
        if dr and not self.vic_step:
            # 如果logging level小于10，保留浏览器以供调试
            if self.logger.level < 10:
                self.logger.warning('【{}】\t由于日志级别为DEV，将保留浏览器以供调试，请自行关闭'.format(execute_id))
            else:
                try:
                    if self.socket_no_response:
                        # 设置Remote Connection超时时间
                        try:
                            _conn = getattr(dr.command_executor, '_conn')
                            _conn.timeout = 5
                        except AttributeError:
                            dr.command_executor.set_timeout(5)
                    # 先通过close方法判断驱动是否可控，然后再关闭
                    self.logger.info('【{}】\t关闭浏览器...'.format(execute_id))
                    dr.close()
                    dr.quit()
                    self.logger.info('【{}】\t已关闭'.format(execute_id))
                except Exception as e:
                    self.logger.error('【{}】\t有一个浏览器无法关闭，请手动关闭。错误信息 => {}'.format(execute_id, e))
            del dr

        if self.force_stop:
            self.case_result.result_state = 4
        elif self.case_result.error_count or self.case_result.result_error:
            self.case_result.result_state = 3
        elif self.case_result.fail_count:
            self.case_result.result_state = 2
            self.case_result.result_message = '失败'
        elif self.case_result.execute_count == 0:
            self.case_result.result_state = 0
            self.case_result.result_message = '跳过'
        else:
            self.case_result.result_state = 1
            self.case_result.result_message = '通过'
        self.end_date = self.case_result.end_date = datetime.datetime.now()
        self.case_result.save()

        self.parent_case_pk_list.pop()
        self.status = 3

        return self
