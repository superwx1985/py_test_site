import threading
import weakref
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures.thread import _worker, _threads_queues
from py_test_site.settings import SUITE_MAX_CONCURRENT_EXECUTE_COUNT


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


SUITE_EXECUTE_POOL = VicThreadPoolExecutor(SUITE_MAX_CONCURRENT_EXECUTE_COUNT or 1)
