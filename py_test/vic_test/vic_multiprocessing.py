# -*- coding: utf-8 -*-
import multiprocessing, os
from time import sleep, ctime

def info(title):
    print ('title is %s' %title)
    print ('module name:', __name__)
    if hasattr(os, 'getppid'):
        print ('parent process:', os.getppid())
        print ('process id:', os.getpid())

def music(name, time=3):
    info('music')
    print ('music start')
    for i in range(time):
        print ('%s playing music: %s %s' %(str(i),name,ctime()))
        sleep(1)
    print(name + ' end')

def movie(name,time=5):
    info('movie')
    print ('movie start')
    for i in range(time):
        print ('%s playing music: %s %s' %(str(i),name,ctime()))
        sleep(1)
    print(name + ' end')
ps =[]
p1 = multiprocessing.Process(target=music, args=('尼玛之歌',3,))
ps.append(p1)
p2 = multiprocessing.Process(target=movie, args=('哈利波特别大',5))
ps.append(p2)
if __name__ == '__main__':
    info('main line')
    for i in ps:
        i.start()
    for i in ps:
        i.join()
    print ('end: %s' % ctime())