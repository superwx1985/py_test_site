'''
Created on 2014年8月29日

@author: viwang
'''
# -*- coding: utf-8 -*-
#===============================================================================
# print([int('0123'),int(12.34),float('12.34'),float(12)])
# print([str(1.23),bool(1),bool('a'),bool(0),bool('')])
# a=abs #变量a指向abs函数
# print(a(-100))
#===============================================================================

#===============================================================================
# def sushu (x):
#     if not isinstance(x, (int)): #isinstance(实例, (类型1, 类型2)):
#         return -1
#     elif x < 2:
#         return -1
#     else:
#         list1 = [2]
#         i = 3
#         while i <= x:
#             j = 2
#             while j <= i:
#                 if j == i:
#                     list1.append(i)
#                     break
#                 if i % j == 0:
#                     break
#                 j += 1
#             i += 1
#         return list1
# 
# x = input('''please enter a whole number greater than 1:
# ''')
# while True:
#       
#     if not x.isdigit() or int(x) < 2: #第二个条件短路，如果第二个条件放到前面，输入字符会报错
#         x = input('''not a whole number or the number is less than 2, please retry:
# ''')
#     else:
#         y = sushu(int(x))
#         z = 0
#         while z < len(y):
#             print(y[z], end='\t')
#             if (z + 1) % 5 == 0:
#                 print('')
#             z += 1
#         break
#===============================================================================

#===============================================================================
# def fact(n):
#     if n==1:
#         return 1
#     return n * fact(n - 1)
# 
# 
# def a(x):
#     i,a=1,1
#     while i<=x:
#         a=a*i
#         i+=1
#     return a
# print(fact(6),a(6))
#===============================================================================

#===============================================================================
# #recursive function
# 
# def fact(n):
#     if n==1:
#         return 1
#     return n * fact(n - 1)
# 
# 
# def a(x):
#     i,a=1,1
#     while i<=x:
#         a=a*i
#         i+=1
#     return a
# print(fact(1),a(1000))
#===============================================================================
