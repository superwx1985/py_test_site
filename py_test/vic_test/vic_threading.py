'''
Created on 2014年9月16日

@author: viwang
'''
# -*- coding: utf-8 -*-
import time, threading, random


al=100
bl=100

def afuckb():
    global bl
    x = random.randint(0,5)
    if x==0:
        print('''A miss B
B ======= %d\n'''%bl)
    elif x==5:
        bl-=10
        print('''A critical hit B deal %d damage
B ======= %d\n''' %(x*2,bl))
    else:
        bl-=x
        print('''A hit B deal %d damage
B ======= %d\n''' %(x,bl))
    if bl<=0:
        print('B is dead, the winner is A\n')
    
def bfucka():
    global al
    x = random.randint(0,5)
    if x==0:
        print('''B miss A
A ======= %d\n'''%al)
    elif x==5:
        al-=10
        print('''B critical hit A deal %d damage
A ======= %d\n''' %(x*2,al))
    else:
        al-=x
        print('''B hit A deal %d damage
A ======= %d\n''' %(x,al))
    if al<=0:
        print('A is dead, the winner is B\n')

def a():
    global al,bl
    while al>0 and bl>0:
        afuckb()
        time.sleep(0.2)
    bl=0

def b():
    global bl,al
    while bl>0 and al>0:
        bfucka()
        time.sleep(0.2)
    al=0

a=threading.Thread(target=a)
b=threading.Thread(target=b)

a.start()
b.start()
a.join()
b.join()