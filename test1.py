import threading
import time

def a(t):
    print('start')
    for i in range(t):
        print(i)
        time.sleep(1)
    print('end')

b = threading.Thread(target=a, args=(5,))

print('start main')
b.start()
b.join(6)
print(b.is_alive())
if b.is_alive():
    pass
print('end main')
