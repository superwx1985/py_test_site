import time
import datetime
import json
import traceback
import logging
import uuid
# import pytz
from py_test.general import vic_variables, vic_public_elements, vic_log, vic_method
from .vic_case import VicCase
from concurrent.futures import wait, CancelledError, TimeoutError as f_TimeoutError
from main.models import Case, SuiteResult, Step
from django.forms.models import model_to_dict
from utils.system import FORCE_STOP
from utils.thread_pool import VicThreadPoolExecutor, RUNNING_SUITES, get_pool, safety_shutdown_pool
from py_test_site.settings import SUITE_MAX_CONCURRENT_EXECUTE_COUNT


class VicSuite:
    def __init__(self, suite, user, execute_uuid=uuid.uuid1(), websocket_sender=None):
        self.logger = logging.getLogger('py_test.{}'.format(execute_uuid))
        self.logger.setLevel(suite.log_level)

        self.websocket_sender = websocket_sender
        if websocket_sender:  # 是否推送websocket
            date_fmt = '%H:%M:%S'
            format_ = logging.Formatter('%(asctime)s [%(threadName)s] - %(message)s', date_fmt)
            ws_handler = vic_log.WebsocketHandler(websocket_sender)
            ws_handler.setFormatter(format_)
            self.logger.addHandler(ws_handler)

        self.suite = suite
        self.user = user
        self.execute_uuid = execute_uuid
        self.suite_force_stop = False  # 用例级别强制停止信号

        self.config = self.suite.config if self.suite.config and self.suite.config.is_active else None
        self.global_variables = vic_variables.Variables(self.logger)
        self.public_elements = vic_public_elements.PublicElements(self.logger)
        self.timeout = suite.timeout
        self.ui_step_interval = suite.ui_step_interval
        self.ui_get_ss = suite.ui_get_ss
        self.log_level = suite.log_level
        self.thread_count = suite.thread_count

        # 初始化suite result
        self.suite_result = SuiteResult.objects.create(
            name=suite.name,
            description=suite.description,
            keyword=suite.keyword,
            timeout=suite.timeout,
            ui_step_interval=suite.ui_step_interval,
            ui_get_ss=suite.ui_get_ss,
            log_level=suite.log_level,
            thread_count=suite.thread_count,
            project=suite.project,

            suite=suite,
            creator=user,
            modifier=user,

            execute_count=0,
            pass_count=0,
            fail_count=0,
            error_count=0,
        )

    # 强制停止标志
    @property
    def force_stop(self):
        if self.suite_force_stop:
            return True
        fs = FORCE_STOP.get(self.execute_uuid)
        if fs and fs == self.user.pk:
            self.suite_force_stop = True
            return True
        else:
            return False

    def execute(self):
        # 记录开始执行时的时间
        self.suite_result.start_date = datetime.datetime.now()

        self.logger.info('开始')
        RUNNING_SUITES[self.execute_uuid] = True

        try:
            # 获取配置json
            if self.config:
                self.suite_result.config = json.dumps(model_to_dict(self.suite.config))

            # 初始化全局变量, 获取变量组json
            self.suite_result.variable_group = None
            if self.suite.variable_group and self.suite.variable_group.is_active:
                variable_objects = self.suite.variable_group.variable_set.all()
                for obj in variable_objects:
                    value = vic_method.replace_special_value(obj.value, self.global_variables, None, self.logger)
                    self.global_variables.set_variable(obj.name, value)
                v_list = list(
                    self.suite.variable_group.variable_set.all().values('pk', 'name', 'description', 'value', 'order'))
                variable_group_dict = model_to_dict(self.suite.variable_group)
                variable_group_dict['variables'] = v_list
                self.suite_result.variable_group = json.dumps(variable_group_dict)

            # 初始化公共元素组，获取元素组json
            self.suite_result.element_group = None
            if self.suite.element_group and self.suite.element_group.is_active:
                element_objects = self.suite.element_group.element_set.all()
                # 获取by映射
                ui_by_dict = {i[0]: i[1] for i in Step.ui_by_list}
                for obj in element_objects:
                    ui_by = ui_by_dict[obj.by]
                    self.public_elements.add_element_info(obj.name, (ui_by, obj.locator))
                v_list = list(
                    self.suite.element_group.element_set.all().values(
                        'pk', 'name', 'description', 'by', 'locator', 'order'))
                element_group_dict = model_to_dict(self.suite.element_group)
                element_group_dict['elements'] = v_list
                self.suite_result.element_group = json.dumps(element_group_dict)

            # 限制进程数
            s_count = SUITE_MAX_CONCURRENT_EXECUTE_COUNT
            if self.thread_count > s_count:
                self.thread_count = s_count
                self.logger.warning('套件线程数超过了服务器允许的最大值【{}】，已被修改为【{}】'.format(s_count, s_count))

            # 获取用例组
            cases = Case.objects.filter(suite=self.suite, is_active=True).order_by('suitevscase__order')

            # 检查配置是否存在
            if not self.config:
                raise ValueError('配置读取出错，请检查配置是否已被删除')

            if len(cases) > 0:

                self.logger.info('准备运行下列{}个用例:'.format(len(cases)))
                vic_cases = list()
                case_order = 0
                for case in cases:
                    case_order += 1
                    vic_cases.append(
                        VicCase(case=case, case_order=case_order, vic_suite=self, execute_str=str(case_order))
                    )
                    self.logger.info('【{}】\tID:{} | {}'.format(case_order, case.pk, case.name))

                self.logger.info('========================================')

                futures = list()

                with VicThreadPoolExecutor(self.thread_count) as pool:  # 保证线程池被关闭

                    for vic_case in vic_cases:
                        futures.append(pool.submit(self.add_vic_case_into_pool, vic_case))
                    future_results = wait(futures)

                    for future_result in future_results.done:
                        case_ = future_result.result()
                        case_result = case_.case_result
                        self.suite_result.execute_count += 1
                        if case_result.result_status == 1:
                            self.suite_result.pass_count += 1
                        elif case_result.result_status == 2:
                            self.suite_result.fail_count += 1
                        elif case_result.result_status == 3:
                            self.suite_result.error_count += 1

            skip_count = (self.suite_result.execute_count - self.suite_result.pass_count
                          - self.suite_result.fail_count - self.suite_result.error_count)

            if self.suite_result.error_count > 0:
                self.suite_result.result_status = 3
            elif self.suite_result.fail_count > 0:
                self.suite_result.result_status = 2
            elif self.suite_result.execute_count == skip_count:
                self.suite_result.result_status = 0
            else:
                self.suite_result.result_status = 1

            self.suite_result.result_message = '执行: {} | 通过: {} | 失败: {} | 出错: {} | 跳过: {}'.format(
                self.suite_result.execute_count, self.suite_result.pass_count, self.suite_result.fail_count,
                self.suite_result.error_count, skip_count)
            self.suite_result.end_date = datetime.datetime.now()
            self.suite_result.save()
        except Exception as e:
            self.suite_result.result_status = 3
            self.suite_result.result_message = '套件执行出错：{}'.format(getattr(e, 'msg', str(e)))
            self.suite_result.result_error = traceback.format_exc()
            self.suite_result.end_date = datetime.datetime.now()
            self.suite_result.save()
        finally:
            RUNNING_SUITES.pop(self.execute_uuid)
            safety_shutdown_pool(self.logger)

            # 清除停止信号
            if FORCE_STOP.get(self.execute_uuid):
                del FORCE_STOP[self.execute_uuid]

        self.logger.info('测试执行完毕')
        self.logger.info('========================================')
        if self.suite_result.result_status == 3:
            self.logger.error(self.suite_result.result_message)
        elif self.suite_result.result_status in (2, 0):
            self.logger.warning(self.suite_result.result_message)
        else:
            self.logger.info(self.suite_result.result_message)
        self.logger.info('耗时: ' + str(self.suite_result.end_date - self.suite_result.start_date))
        self.logger.info('========================================')
        self.logger.info('结束')

        # 关闭日志文件句柄
        for h in self.logger.handlers:
            h.close()

        return self

    def add_vic_case_into_pool(self, vic_case, check_interval=10, timeout=None):
        task = get_pool(self.logger).submit(vic_case.execute)
        self.logger.debug('【{}】\t用例【{}】进入队列'.format(vic_case.execute_str, vic_case.name))

        start_time = time.time()
        while True:
            try:
                task.result(timeout=check_interval)
            except CancelledError:
                elapsed_time = time.time() - start_time
                self.logger.warning('【{}】\t用例【{}】已在队列{:.1f}秒，已被取消'.format(
                    vic_case.execute_str, vic_case.name, elapsed_time))
                break
            except f_TimeoutError:
                if self.force_stop:
                    task.cancel()
                    vic_case.case_result.result_status = 0
                    vic_case.case_result.result_message = '接收到强制停止信号，用例被取消执行'
                    vic_case.case_result.end_date = datetime.datetime.now()
                    vic_case.case_result.save()
                    break
                elapsed_time = time.time() - start_time
                if task.running():
                    self.logger.debug('【{}】\t用例【{}】已在队列{:.1f}秒，执行中...'.format(
                        vic_case.execute_str, vic_case.name, elapsed_time))
                else:
                    if timeout and elapsed_time > timeout:
                        self.logger.warning('【{}】\t用例【{}】已在队列{:.1f}秒，尝试取消'.format(
                            vic_case.execute_str, vic_case.name, elapsed_time))
                        _success = task.cancel()
                        vic_case.case_result.result_status = 3
                        vic_case.case_result.result_error = '线程等待超时，可能由于服务器线程池队列已满，用例被取消执行'
                        vic_case.case_result.end_date = datetime.datetime.now()
                        vic_case.case_result.save()
                        if not _success:
                            self.logger.warning('【{}】\t用例【{}】取消失败，发送用例级别强制停止信号'.format(
                                vic_case.execute_str, vic_case.name))
                            vic_case.case_force_stop = True
                            break
                    else:
                        self.logger.info('【{}】\t用例【{}】已在队列{:.1f}秒，排队中...'.format(
                            vic_case.execute_str, vic_case.name, elapsed_time))
            else:
                break

        return vic_case


if __name__ == '__main__':
    pass