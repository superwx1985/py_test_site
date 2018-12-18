from concurrent.futures import ThreadPoolExecutor, wait
from time import sleep
# from utils.thread_pool import SUITE_EXECUTE_POOL
import random
import logging
import sys
import threading
from utils.log import NonWarningFilter

logger = logging.getLogger()
f1 = logging.Formatter('%(asctime)s [%(threadName)s]\t[%(lineno)d]\t%(message)s')
h1 = logging.StreamHandler(sys.stdout)
h2 = logging.StreamHandler(sys.stderr)
h1.setLevel(logging.INFO)
h2.setLevel(logging.WARNING)
h1.setFormatter(f1)
h2.setFormatter(f1)
h1.addFilter(NonWarningFilter())
logger.addHandler(h1)
logger.addHandler(h2)
logger.setLevel(logging.INFO)




class VicCase:
    def __init__(self, name):
        self.name = name

    def execute(self, para, _pool):
        logger.warning('{} - {} start'.format(self.name, para))
        sleep(1)

        logger.info(
            'A name = [{}], active_count = [{}], parent_pool_threads = [{}/{}], threads = [{}/{}], SUITE_threads = [{}/{}]'.format(
                _pool.name,
                threading.active_count(),
                len(_pool.parent_pool.active_threads),
                len(_pool.parent_pool._threads),
                len(_pool.active_threads),
                len(_pool._threads),
                len(SUITE_EXECUTE_POOL.active_threads),
                len(SUITE_EXECUTE_POOL._threads),
            )
        )
        # if _pool.reactivate_threads():
        #     logger.info(
        #         'inside change name = [{}], active_count = [{}], parent_pool_threads = [{}/{}], threads = [{}/{}], SUITE_threads = [{}/{}]'.format(
        #             _pool.name,
        #             threading.active_count(),
        #             len(_pool.parent_pool.active_threads),
        #             len(_pool.parent_pool._threads),
        #             len(_pool.active_threads),
        #             len(_pool._threads),
        #             len(SUITE_EXECUTE_POOL.active_threads),
        #             len(SUITE_EXECUTE_POOL._threads),
        #         )
        #     )

        sleep(3)

        logger.info('{} - {} end'.format(self.name, para))
        sleep(1)
        return self.name


def append_case(case, case_order, _pool, timeout=None):

    futures = list()
    futures.append(SUITE_EXECUTE_POOL.submit(case.execute, case_order, _pool))

    _result = 'N/A'
    i = 0
    while True:
        i += 1
        future_results = wait(futures, timeout=timeout)
        if future_results.done:
            _result = future_results.done.pop().result()
            break
        else:
            logger.info('{}呵呵，【{}】还没跑完'.format(i, case.name))
        if i == 3:
            logger.info('试试把【{}】停下来，停了？{}'.format(case.name, futures.pop().cancel()))
            break


    # logger.info(
    #     'B name = [{}], active_count = [{}], parent_pool_threads = [{}/{}], threads = [{}/{}], SUITE_threads = [{}/{}]'.format(
    #         _pool.name,
    #         threading.active_count(),
    #         len(_pool.parent_pool.active_threads),
    #         len(_pool.parent_pool._threads),
    #         len(_pool.active_threads),
    #         len(_pool._threads),
    #         len(SUITE_EXECUTE_POOL.active_threads),
    #         len(SUITE_EXECUTE_POOL._threads),
    #     )
    # )
    # sleep(1)
    # if SUITE_EXECUTE_POOL.reactivate_threads():
    #     logger.info(
    #         'change: name = [{}], active_count = [{}], parent_pool_threads = [{}/{}], threads = [{}/{}], SUITE_threads = [{}/{}]'.format(
    #             _pool.name,
    #             threading.active_count(),
    #             len(_pool.parent_pool.active_threads),
    #             len(_pool.parent_pool._threads),
    #             len(_pool.active_threads),
    #             len(_pool._threads),
    #             len(SUITE_EXECUTE_POOL.active_threads),
    #             len(SUITE_EXECUTE_POOL._threads),
    #         )
    #     )

    return _result


def execute_suite(_pool, case_name_list, timeout=None):

    vic_cases = list()

    for case_name in case_name_list:
        vic_cases.append(VicCase(case_name))


    case_order = 0
    futures = list()
    suite_result = list()

    for case in vic_cases:
        case_order += 1
        futures.append(_pool.submit(append_case, case, case_order, _pool, timeout))
        # futures.append(_pool.submit(case.execute, case_order, _pool))
    try:
        future_results = wait(futures)
    except Exception as e:
        logger.error(e)
    else:

        for future_result in future_results.done:
            suite_result.append(future_result.result())
            # logger.info('suite result: {}'.format(case_))
    finally:
        _pool.shutdown()
    return suite_result

from concurrent.futures.thread import _worker, _threads_queues
import weakref



class VicThreadPoolExecutor(ThreadPoolExecutor):
    def __init__(self, max_workers, name='', parent_pool=None):
        self.name = name
        self.parent_pool = parent_pool
        self._cond = threading.Condition()
        self._lock = threading.Lock()
        super().__init__(max_workers)

    @property
    def active_threads(self):
        ts = set()
        for t in self._threads:
            if t.is_alive():
                ts.add(t)
        return ts

    # def reactivate_threads(self):
    #     self._lock.acquire()
    #     if len(self._threads) < self._max_workers:
    #         self._adjust_thread_count()
    #         print('[{}/{}]'.format(len(self._threads), self._max_workers))
    #     active_threads = self.active_threads
    #     if len(active_threads) < len(self._threads):
    #         self._threads = active_threads
    #         self._adjust_thread_count()
    #         self._lock.release()
    #         return True
    #     else:
    #         self._lock.release()
    #         return False

    def _adjust_thread_count(self):

        def weakref_cb(_, q=self._work_queue):
            q.put(None)

        if len(self._threads) < self._max_workers:
            t = threading.Thread(target=_worker,
                                 args=(weakref.ref(self, weakref_cb),
                                       self._work_queue))
            # t.daemon = True
            t.start()
            self._threads.add(t)
            _threads_queues[t] = self._work_queue



SUITE_EXECUTE_POOL = VicThreadPoolExecutor(4)
__pool = VicThreadPoolExecutor(3)


futures = list()

futures.append(__pool.submit(execute_suite, VicThreadPoolExecutor(7, '1', __pool), [101,102,103,104,105,106,107,108,], 2))

sleep(1)

futures.append(__pool.submit(execute_suite, VicThreadPoolExecutor(4, '2', __pool), [201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,]))

# sleep(1)

futures.append(__pool.submit(execute_suite, VicThreadPoolExecutor(3, '3', __pool), [301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,]))

try:
    main_futures_results = wait(futures)
    for r in main_futures_results.done:
        print(r.result())
except:
    raise
finally:



    print(1, '=====================', threading.active_count())
    __pool.shutdown()
    print(2, '=====================', threading.active_count())

    SUITE_EXECUTE_POOL.shutdown()
    print(3, '=====================', threading.active_count())
