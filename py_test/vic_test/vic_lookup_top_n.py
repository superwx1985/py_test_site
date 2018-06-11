'''
Created on 2014年10月31日

@author: viwang
'''
# -*- coding: utf-8 -*-

def top(list_,n,group):
    if len(list_)<n:
        return list_
    time = int(len(list_)/group)+1
    result = list_[0:n]
    for i in range(time):
        min_ = result[0]
        min_idx = 0
        for index, value in enumerate(result):
            if value < min_:
                min_ = value
                min_idx = index
        if i == 0:
            list2 = list_[n:(i+1)*group]
        else:
            list2 = list_[i*group:(i+1)*group]
        for j in list2:
            if j > min_:
                del result[min_idx]
                result.append(j)
                min_ = result[0]
                min_idx = 0
                for index, value in enumerate(result):
                    if value < min_:
                        min_ = value
                        min_idx = index
    return result
        
list_ = [12,456,78,9877,44,1312,789,12313,752,23,789,87,0,7796,13,797]
list_2 = [12,456,78,9877,44,1312,78,78,11]
print(top(list_,2,1))  