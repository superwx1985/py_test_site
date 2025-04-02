import time
import datetime
import traceback
import logging
import uuid
import threading

from main.views.gtm import get_gtm_data_
from py_test.general import vic_variables, vic_public_elements, vic_log, vic_method, vic_case as vc
from .public_items import status_str_dict
from concurrent.futures import wait, CancelledError, TimeoutError as f_TimeoutError
from main.models import Case, SuiteResult, Step, error_handle_dict
from django.forms.models import model_to_dict
from utils.system import RUNNING_SUITES
from utils.thread_pool import VicThreadPoolExecutor, get_pool, safety_shutdown_pool
from django.conf import settings


class VicSuite:
    def __init__(self, suite, user, execute_uuid=uuid.uuid1(), websocket_sender=None):
        self.logger = logging.getLogger('py_test.{}'.format(execute_uuid))
        self.logger.setLevel(suite.log_level)

        self.websocket_sender = websocket_sender
        if websocket_sender:  # 是否推送websocket
            formatter_config = settings.LOGGING['formatters']['websocket']
            format_str = formatter_config['format']
            date_fmt = formatter_config.get('datefmt', None)
            formatter = logging.Formatter(format_str, date_fmt)
            ws_handler = vic_log.WebsocketHandler(websocket_sender)
            ws_handler.setFormatter(formatter)
            self.logger.addHandler(ws_handler)

        self.suite = suite
        self.name = suite.name
        self.user = user
        self.execute_uuid = execute_uuid
        self.force_stop_signal = False  # 强制停止信号
        self.pause_lock = threading.Lock()
        self.vic_cases = []
        self.status = 0
        self.init_date = datetime.datetime.now()
        self.start_date = None

        self.config = self.suite.config if self.suite.config and self.suite.config.is_active else None
        self.global_variables = vic_variables.Variables(self.logger)
        self.public_elements = vic_public_elements.PublicElements(self.logger)
        self.timeout = suite.timeout
        self.ui_step_interval = suite.ui_step_interval
        self.ui_get_ss = suite.ui_get_ss
        self.log_level = suite.log_level
        self.thread_count = suite.thread_count
        self.error_handle = error_handle_dict.get(suite.error_handle, 'stop')

        # 初始化suite result
        _snapshot = model_to_dict(suite) if suite else None
        _snapshot['case'] = [x.pk for x in _snapshot['case']]
        self.suite_result = SuiteResult.objects.create(
            name=suite.name,
            description=suite.description,
            keyword=suite.keyword,
            project=suite.project,

            suite=suite,
            creator=user,
            modifier=user,

            execute_count=0,
            pass_count=0,
            fail_count=0,
            error_count=0,
            stop_count=0,

            snapshot=_snapshot,
        )

    # 强制停止标志
    @property
    def force_stop(self):
        if self.force_stop_signal:
            self.status = 3
            return True
        else:
            return False

    def continue_(self):
        with self.pause_lock:
            _continue = True
            for vc in self.vic_cases:
                if vc.status == 2:
                    _continue = False
                    break
            if _continue:
                self.websocket_sender('套件已继续', 20, _type='continue')
                if 1 < self.status <= 2:
                    self.status = 1

    @property
    def status_str(self):
        return status_str_dict[self.status]

    def execute(self):
        # 记录开始执行时的时间
        self.start_date = self.suite_result.start_date = datetime.datetime.now()
        self.status = 1
        self.logger.info('开始测试，结果ID[{}]'.format(self.suite_result.pk))
        RUNNING_SUITES.add_suite(self.execute_uuid, self)

        try:
            # 获取配置json
            if self.config:
                self.suite_result.config = model_to_dict(self.suite.config)

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
                self.suite_result.variable_group = variable_group_dict

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
                self.suite_result.element_group = element_group_dict

            # 限制进程数
            s_count = settings.SUITE_MAX_CONCURRENT_EXECUTE_COUNT
            if self.thread_count > s_count:
                self.thread_count = s_count
                self.logger.warning('套件线程数超过了服务器允许的最大值【{}】，已被修改为【{}】'.format(s_count, s_count))

            # 获取用例组
            cases = Case.objects.filter(suite=self.suite, is_active=True).order_by('suitevscase__order')

            # 检查配置是否存在
            if not self.config:
                raise ValueError('配置读取出错，请检查配置是否已被删除')

            if cases:
                self.logger.info("初始化用例列表...")
                case_order = 0
                for case in cases:
                    if case.data_set and case.data_set.is_active:  # 拆分数据组
                        data_set_cases = vc.get_case_list(case, self.logger)
                        for data_set_case in data_set_cases:
                            case_order = self.add_case(case_order, data_set_case[0], data_set_case[1])
                    else:
                        case_order = self.add_case(case_order, case)

                self.logger.info(f"共{len(self.vic_cases)}个用例")
                self.logger.info('========================================')

                futures = []

                with VicThreadPoolExecutor(max_workers=self.thread_count) as pool:  # 保证线程池被关闭

                    for vic_case in self.vic_cases:
                        futures.append(pool.submit(self.add_vic_case_into_pool, vic_case, self.timeout))
                    future_results = wait(futures)

                    for future_result in future_results.done:
                        case_ = future_result.result()
                        case_result = case_.case_result
                        self.suite_result.execute_count += 1
                        if case_result.result_state == 1:
                            self.suite_result.pass_count += 1
                        elif case_result.result_state == 2:
                            self.suite_result.fail_count += 1
                        elif case_result.result_state == 3:
                            self.suite_result.error_count += 1
                        elif case_result.result_state == 4:
                            self.suite_result.stop_count += 1

            ignore_count = (self.suite_result.execute_count - self.suite_result.pass_count
                            - self.suite_result.fail_count - self.suite_result.error_count
                            - self.suite_result.stop_count)

            if self.suite_result.error_count:
                self.suite_result.result_state = 3
            elif self.suite_result.fail_count:
                self.suite_result.result_state = 2
            elif self.force_stop or self.suite_result.stop_count:
                self.suite_result.result_state = 4
            elif self.suite_result.execute_count == ignore_count:
                self.suite_result.result_state = 0
            else:
                self.suite_result.result_state = 1

            self.suite_result.result_message = '执行: {} | 通过: {} | 失败: {} | 异常: {} | 中止: {} | 忽略: {}'.format(
                self.suite_result.execute_count, self.suite_result.pass_count, self.suite_result.fail_count,
                self.suite_result.error_count, self.suite_result.stop_count, ignore_count)
            self.suite_result.end_date = datetime.datetime.now()
            self.suite_result.save()
        except Exception as e:
            self.suite_result.result_state = 3
            self.suite_result.result_message = '套件执行出错：{}'.format(getattr(e, 'msg', str(e)))
            self.suite_result.result_error = traceback.format_exc()
            self.suite_result.end_date = datetime.datetime.now()
            self.suite_result.save()
        finally:
            RUNNING_SUITES.remove_suite(self.execute_uuid)
            safety_shutdown_pool(self.logger)

            self.logger.info('测试执行完毕，结果ID[{}]'.format(self.suite_result.pk))
            self.logger.info('========================================')
            if self.suite_result.result_state == 3:
                self.logger.error(self.suite_result.result_message)
            elif self.suite_result.result_state != 1:
                self.logger.warning(self.suite_result.result_message)
            else:
                self.logger.info(self.suite_result.result_message)
            self.logger.info('耗时: ' + str(self.suite_result.end_date - self.suite_result.start_date))
            self.logger.info('========================================')
            self.logger.info('结束')

            # 关闭日志文件句柄
            for h in self.logger.handlers:
                h.close()

            self.status = 4

        return self

    def add_vic_case_into_pool(self, vic_case, timeout=None):
        if vic_case.data_set_dict and vic_case.data_set_dict.get('2_name'):
            case_name = vic_case.data_set_dict['2_name']
        else:
            case_name = vic_case.name
        self.logger.info('【{}】\t用例【{}】进入队列'.format(vic_case.execute_str, case_name))
        task = get_pool(self.logger).submit(vic_case.execute)
        # import pdb
        # pdb.set_trace()
        start_time = time.time()
        while True:
            try:
                task.result(timeout=timeout)
            except CancelledError:
                elapsed_time = time.time() - start_time
                self.logger.warning('【{}】\t用例【{}】已在队列{:.1f}秒，已被取消'.format(
                    vic_case.execute_str, case_name, elapsed_time))
                break
            except f_TimeoutError:
                if self.force_stop:
                    task.cancel()
                    vic_case.case_result.result_state = 0
                    vic_case.case_result.result_message = '接收到强制停止信号，用例被取消执行'
                    vic_case.case_result.end_date = datetime.datetime.now()
                    vic_case.case_result.save()
                    break
                elapsed_time = time.time() - start_time
                if task.running():
                    self.logger.debug('【{}】\t用例【{}】已在队列{:.1f}秒，执行中...'.format(
                        vic_case.execute_str, case_name, elapsed_time))
                else:
                    if timeout and elapsed_time > timeout:
                        self.logger.warning('【{}】\t用例【{}】已在队列{:.1f}秒，尝试取消'.format(
                            vic_case.execute_str, case_name, elapsed_time))
                        _success = task.cancel()
                        vic_case.case_result.result_state = 3
                        vic_case.case_result.result_message = "超时"
                        vic_case.case_result.result_error = '线程等待超时，可能由于服务器线程池已满，且套件超时设置过短，测试被取消执行'
                        vic_case.case_result.end_date = datetime.datetime.now()
                        vic_case.case_result.save()
                        if not _success:
                            self.logger.warning('【{}】\t用例【{}】取消失败，发送用例级别强制停止信号'.format(
                                vic_case.execute_str, case_name))
                            vic_case.force_stop = True
                            break
                    else:
                        self.logger.info('【{}】\t用例【{}】已在队列{:.1f}秒，排队中...'.format(
                            vic_case.execute_str, case_name, elapsed_time))
            else:
                break

        return vic_case

    def add_case(self, case_order, case, data_set_dict=None):
        case_order += 1
        self.vic_cases.append(
            vc.VicCase(case=case, case_order=case_order, vic_suite=self, execute_str=str(case_order),
                    data_set_dict=data_set_dict)
        )
        name = data_set_dict['2_name'] if data_set_dict else case.name
        self.logger.info(f'【{case_order}】\tID:{case.pk} | {name}')
        return case_order


if __name__ == '__main__':
    pass
