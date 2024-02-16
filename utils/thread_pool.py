import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from py_test_site.settings import SUITE_MAX_CONCURRENT_EXECUTE_COUNT
from .system import RUNNING_SUITES


class VicThreadPoolExecutor(ThreadPoolExecutor):
    # def __init__(self, max_workers=None, name='', parent_pool=None):
    #     self.name = name
    #     self.parent_pool = parent_pool
    #     super().__init__(max_workers)

    @property
    def active_threads(self):
        ts = set()
        for t in self._threads:
            if t.is_alive():
                ts.add(t)
        return ts

    def work_queue_empty_shutdown(self):
        if self._work_queue.empty():
            self.shutdown()
            return True
        else:
            return False


SUITE_EXECUTE_POOL = None
lock = threading.Lock()


def get_pool(logger=logging.getLogger('py_test.{}')):
    global SUITE_EXECUTE_POOL
    if lock.locked():
        msg = '线程被锁定'
    else:
        msg = '线程未被锁定'
    logger.debug('{}，公用线程池：{}，当前线程总数：{}'.format(msg, SUITE_EXECUTE_POOL, threading.active_count()))
    with lock:
        if not SUITE_EXECUTE_POOL or (not RUNNING_SUITES.get_suites() and SUITE_EXECUTE_POOL.work_queue_empty_shutdown()):
            SUITE_EXECUTE_POOL = VicThreadPoolExecutor(SUITE_MAX_CONCURRENT_EXECUTE_COUNT or 1)
            logger.debug('新建线程池')
    return SUITE_EXECUTE_POOL


def safety_shutdown_pool(logger=logging.getLogger('py_test.{}')):
    global SUITE_EXECUTE_POOL
    with lock:
        if SUITE_EXECUTE_POOL and not RUNNING_SUITES.get_suites() and SUITE_EXECUTE_POOL.work_queue_empty_shutdown():
            # del SUITE_EXECUTE_POOL
            SUITE_EXECUTE_POOL = None
            msg = '关闭线程池'
        else:
            msg = '保留线程池'
    logger.debug('{}，公用线程池：{}，当前线程总数：{}'.format(msg, SUITE_EXECUTE_POOL, threading.active_count()))
