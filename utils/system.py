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
        success = False
        msg = '套件不存在，无法中止'
        if execute_uuid in self.suites:
            with lock:
                if execute_uuid in self.suites:
                    suite = self.suites[execute_uuid]
                    if not user or user == suite.user:
                        if suite.status < 3:
                            suite.status = 3
                            suite.force_stop_signal = True
                            success = True
                            msg = '已发送中止信号'
                        else:
                            msg = '套件正在中止或已经结束'
                    else:
                        msg = '该用户无中止执行权限'

        return success, msg

    def pause_suite(self, execute_uuid, user=None):
        success = False
        msg = '套件不存在，无法暂停'
        if execute_uuid in self.suites:
            with lock:
                if execute_uuid in self.suites:
                    suite = self.suites[execute_uuid]
                    if not user or user == suite.user:
                        if suite.status == 0:
                            msg = '套件未运行'
                        elif 0 < suite.status < 2:
                            for case in suite.vic_cases:
                                if case.status == 1:
                                    case.pause_signal = True
                            suite.status = 2
                            success = True
                            msg = '已发送暂停信号'
                        elif suite.status == 2:
                            success = True
                            msg = '套件已暂停'
                        elif suite.status == 4:
                            msg = '套件已结束'
                        else:
                            msg = f'套件状态为{suite.status}，可能正在切换用例'
                    else:
                        msg = '该用户无中止执行权限'

        return success, msg

    def continue_suite(self, execute_uuid, user=None):
        success = False
        msg = '套件不存在，无法继续'
        if execute_uuid in self.suites:
            with lock:
                if execute_uuid in self.suites:
                    suite = self.suites[execute_uuid]
                    if not user or user == suite.user:
                        if suite.status == 0:
                            msg = '套件未运行'
                        elif 1 < suite.status <= 2:
                            for case in suite.vic_cases:
                                if case.status == 2 or case.pause_signal:
                                    case.pause_signal = False
                                    case.continue_signal = True
                                    success = True
                            if success:
                                msg = '已发送继续信号'
                            else:
                                msg = '套件没有暂停中的用例'
                        elif suite.status == 4:
                            msg = '套件已结束'
                        else:
                            msg = f'套件状态为{suite.status}，可能正在切换用例'
                    else:
                        msg = '该用户无中止执行权限'

        return success, msg

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
        success = False
        msg = '套件不存在，无法中止'
        if execute_uuid in self.suites:
            with lock:
                if execute_uuid in self.suites:
                    suite = self.suites[execute_uuid]
                    i = case_order - 1
                    if 0 <= i < len(suite.vic_cases):
                        if not user or user == suite.user:
                            if suite.vic_cases[i].status < 3:
                                suite.vic_cases[i].status = 3
                                suite.vic_cases[i].force_stop_signal = True
                                success = True
                                msg = '已发送中止信号'
                            else:
                                msg = '用例正在中止或已经结束'
                        else:
                            msg = '该用户无中止执行权限'
                    else:
                        msg = '用例不存在，无法中止'

        return success, msg

    def pause_case(self, execute_uuid, case_order, user=None):
        success = False
        msg = '套件不存在，无法暂停'
        if execute_uuid in self.suites:
            with lock:
                if execute_uuid in self.suites:
                    suite = self.suites[execute_uuid]
                    i = case_order - 1
                    if 0 <= i < len(suite.vic_cases):
                        if not user or user == suite.user:
                            case = suite.vic_cases[i]
                            if case.status == 0:
                                msg = '用例未运行'
                            elif case.status == 1:
                                case.pause_signal = True
                                success = True
                                msg = '已发送暂停信号'
                            elif case.status == 2:
                                success = True
                                msg = '用例已暂停'
                            else:
                                msg = '用例已结束'
                        else:
                            msg = '该用户无中止执行权限'
                    else:
                        msg = '用例不存在，无法暂停'

        return success, msg

    def continue_case(self, execute_uuid, case_order, user=None):
        success = False
        msg = '套件不存在，无法继续'
        if execute_uuid in self.suites:
            with lock:
                if execute_uuid in self.suites:
                    suite = self.suites[execute_uuid]
                    i = case_order - 1
                    if 0 <= i < len(suite.vic_cases):
                        if not user or user == suite.user:
                            case = suite.vic_cases[i]
                            if case.status == 0:
                                msg = '用例未运行'
                            elif case.status == 1:
                                msg = '用例未暂停'
                            elif case.status == 2 or case.pause_signal:
                                case.pause_signal = False
                                case.continue_signal = True
                                success = True
                                msg = '已发送继续信号'
                            else:
                                msg = '用例已结束'
                        else:
                            msg = '该用户无中止执行权限'
                    else:
                        msg = '用例不存在，无法继续'

        return success, msg


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

