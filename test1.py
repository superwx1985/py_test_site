import datetime
import time

a = datetime.datetime.now()
time.sleep(0.5)
b = datetime.datetime.now()

c = b - a

print(c)

from datetime import timedelta

d = timedelta(days=9999)

print(d)

