import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait, as_completed


def a(count):
    print('a start')
    for i in range(count):
        print('a>', i)
        time.sleep(1)
    print('a end')
    return i

pool = ThreadPoolExecutor(1)
futures = list()
futures.append(pool.submit(a, 30))
# t = threading.Thread(target=get_driver_, args=(config, timeout, logger), daemon=True)
future_results = as_completed(futures, timeout=3)
for future_result in future_results:
    dr = future_result.result()
    print(1111, dr, type(dr))
pool.shutdown()
print(dr)