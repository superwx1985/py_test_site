import threading
import copy


lock = threading.Lock()


class RunningSuites:
    def __init__(self):
        self.suites = dict()

    def add_suite(self, execute_uuid, suite):
        with lock:
            if execute_uuid not in self.suites:
                self.suites[execute_uuid] = suite

    def remove_suite(self, execute_uuid):
        if execute_uuid in self.suites:
            with lock:
                if execute_uuid in self.suites:
                    self.suites.pop(execute_uuid)

    def stop_suite(self, execute_uuid, user=None):
        force_stop = False
        msg = '任务不存在，无法中止'
        if execute_uuid in self.suites:
            with lock:
                if execute_uuid in self.suites:
                    suite = self.suites[execute_uuid]
                    if not user or user == suite.user:
                        if suite.status < 2:
                            suite.status = 2
                            suite.force_stop_ = True
                            force_stop = True
                            msg = '已发送中止信号'
                        else:
                            msg = '此任务正在中止或已经结束'
                    else:
                        msg = '该用户无中止执行权限'

        return force_stop, msg

    def get_suites(self):
        with lock:
            suites = copy.copy(self.suites)
        return suites

    def get_suite(self, execute_uuid):
        suite = None
        if execute_uuid in self.suites:
            with lock:
                if execute_uuid in self.suites:
                    suite = copy.copy(self.suites[execute_uuid])
        return suite

    def stop_case(self, execute_uuid, case_order, user=None):
        force_stop = False
        msg = '任务不存在，无法中止'
        if execute_uuid in self.suites:
            with lock:
                if execute_uuid in self.suites:
                    suite = self.suites[execute_uuid]
                    i = case_order - 1
                    if 0 <= i < len(suite.vic_cases):
                        if not user or user == suite.user:
                            if suite.vic_cases[i].status < 2:
                                suite.vic_cases[i].status = 2
                                suite.vic_cases[i].force_stop_ = True
                                force_stop = True
                                msg = '已发送中止信号'
                            else:
                                msg = '此任务正在中止或已经结束'
                        else:
                            msg = '该用户无中止执行权限'

        return force_stop, msg


# 运行中套件
RUNNING_SUITES = RunningSuites()


# 获取当前函数名称
def get_current_function_name():
    import inspect
    return inspect.stack()[1][3]


# 通过函数名称获取函数
def get_function_with_name(space, name):
    # space = sys.modules[__name__]
    return getattr(space, name)

