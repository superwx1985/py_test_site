'''
Created on 2014年9月24日

@author: viwang
'''
# -*- coding: utf-8 -*-

#===============================================================================
# #file = open('text1.txt', mode='r')  # 相对路径
# file= open('D:/viwang/workspace/PyTest01/vic_test/text1.txt', mode='r') #绝对路径
# #file= open('D:\\viwang\\workspace\\PyTest01\\vic_test\\text1.txt', mode='r') #注意斜杠的两种写法
# data = file.readlines()
# file.close()
#        
# for line in data:
#         print(line)
#===============================================================================

#===============================================================================
# import csv
# with open('D:/viwang/workspace/PyTest01/vic_test/csv1.csv', mode='r', newline='') as csvfile: 
# #用with是用来保证运行中出错也可以正确关闭文件的，mode是指定打开方式，newline是指定换行符处理方式
#     data = csv.reader(csvfile, delimiter=',', quotechar='"') 
# #delimiter指定分隔符，默认是','，quotechar指定引用符，默认是'"'(双引号)，意思是两个'"'之间的内容会无视换行，分隔等符号，直接输出为一个元素
#     for line in data:
#         print(line)
#         for column in line:
#             print(column)
#===============================================================================

#===============================================================================
# from xml.dom import minidom 
# 
# dom = minidom.parse('D:/viwang/workspace/PyTest01/vic_test/xml1.xml')
# root = dom.documentElement
# elements=root.getElementsByTagName('item')
# for x in elements:
#     print(x.nodeName,x.getAttribute('id'))
# element = root.getElementsByTagName('caption')[0]
# print(element.firstChild.data)
#===============================================================================


#===============================================================================
# 操作excel
# 获取一个工作表
# 
#         table = data.sheets()[0]          #通过索引顺序获取
#  
#         table = data.sheet_by_index(0) #通过索引顺序获取
#  
# 
#         table = data.sheet_by_name(u'Sheet1')#通过名称获取
#  
#         获取整行和整列的值（数组）
#  　　
#          table.row_values(i)
#  
#          table.col_values(i)
#  
#         获取行数和列数
# 　　
#         nrows = table.nrows
#  
#         ncols = table.ncols
#        
#         循环行列表数据
#         for i in range(nrows ):
#       print table.row_values(i)
#  
# 单元格
# cell_A1 = table.cell(0,0).value
#  
# cell_C4 = table.cell(2,3).value
#  
# 使用行列索引
# cell_A1 = table.row(0)[0].value
#  
# cell_A2 = table.col(1)[0].value
#  
# 简单的写入
# row = 0
#  
# col = 0
#  
# # 类型 0 empty,1 string, 2 number, 3 date, 4 boolean, 5 error
# ctype = 1 value = '单元格的值'
#  
# xf = 0 # 扩展的格式化
#  
# table.put_cell(row, col, ctype, value, xf)
#  
# table.cell(0,0)  #单元格的值'
#  
# table.cell(0,0).value #单元格的值'
#===============================================================================
# import xlrd
#
# def test_get_excle_data(dir='D:/vic/workspace/PyTest01/vic_test/excel1.xlsx'):
#     workbook = xlrd.open_workbook(dir)
#     sheep = workbook.sheet_by_name('Sheet1')
#     print(sheep.row_values(0))
#     print(sheep.col_values(0))
#     print(sheep.cell(1,0))
#     print(sheep.cell(1,0).value)
#     for i in range(0,sheep.nrows):
#         for j in range(0,sheep.ncols):
#             print(sheep.cell(i,j).value, '\t', end='')
#             if j+1 == sheep.ncols:
#                 print('\n')

#===============================================================================
# 列数转英文列名
# x=12116
# map_ = {0: 'err', 1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J', 11: 'K', 12: 'L', 13: 'M', 14: 'N', 15: 'O', 16: 'P', 17: 'Q', 18: 'R', 19: 'S', 20: 'T', 21: 'U', 22: 'V', 23: 'W', 24: 'X', 25: 'Y', 26: 'Z'}
# s=''
# print(x,'=======>')
# while(True):
#     if x<27:
#         print(x)
#         print(map_[x])
#         s=s+map_[x]
#         break
#     y = int(x/26)
#     if y > 26:
#         if x%26 == 0:
#             print(x%26)
#             print(map_[26])
#             s=s+map_[26]
#             x = y-1
#             continue
#         print(x%26)
#         print(map_[x%26])
#         s=s+map_[x%26]
#         x = y
#         continue
#     if x%26 == 0:
#         print(y-1,26)
#         print(map_[y-1],map_[26])
#         s=s+map_[26]+map_[y-1]
#     else:    
#         print(y,x%26)
#         print(map_[y],map_[x%26])
#         s=s+map_[x%26]+map_[y]
#     x = y
#     if y<=26:
#         break
# s=s[::-1]
# print(s)
#===============================================================================
# import xlrd  # 读取excel数据，需安装xlrd
# import os
#
# bace_dir = os.path.dirname(__file__)
# def get_excle_data(filename, sheet_name, print_=False):
#     data = {}
#     map_ = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J', 11: 'K', 12: 'L', 13: 'M', 14: 'N', 15: 'O', 16: 'P', 17: 'Q', 18: 'R', 19: 'S', 20: 'T', 21: 'U', 22: 'V', 23: 'W', 24: 'X', 25: 'Y', 26: 'Z'}
#     with xlrd.open_workbook(filename) as workbook:
#         sheet = workbook.sheet_by_name(sheet_name)
#         data['file']=filename
#         data['sheet']=sheet_name
#         data['rows']=sheet.nrows
#         data['columns']=sheet.ncols
#         if print_:
#             print('open excel file ==> %s\nload sheet ==> %s\nthis file has %s rows, %s columns' %(data['file'],data['sheet'],data['rows'],data['columns']))
#         for r in range(0, sheet.nrows):
#             rname = str(r+1)
#             for c in range(0, sheet.ncols):
#                 x = c + 1
#                 s = ''
#                 while(True):
#                     if x < 27:
#                         s = s + map_[x]
#                         break
#                     y = int(x/26)
#                     if y > 26:
#                         if x%26 == 0:
#                             s= s + map_[26]
#                             x = y - 1
#                             continue
#                         s = s + map_[x%26]
#                         x = y
#                         continue
#                     if x%26 == 0:
#                         s = s + map_[26] + map_[y-1]
#                     else:
#                         s = s + map_[x%26] + map_[y]
#                     x = y
#                     if y <= 26:
#                         break
#                 cname = s[::-1]
#                 data[cname + rname] = sheet.cell(r, c).value
#                 if print_:
#                     print('['+cname + str(r+1)+']'+str(sheet.cell(r,c).value)+'\t\t', end='')
#                     if c+1 == sheet.ncols:
#                         print('\n')
#     return data
