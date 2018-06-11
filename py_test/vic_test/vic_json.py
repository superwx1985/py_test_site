'''
Created on 2016年1月28日

@author: vic
'''
def remove_linefeed(string):
    string = string.replace('\n','')
    return string

def remove_blank(string):
    string = string.replace(' ','')
    return string

def format_json(string):
    if string.count('\"')%2 != 0:
        raise ValueError('unpaired double quotes')
    new_str=''
    quote = 0
    blank = 0
    for i in string:
        if quote:
            new_str = new_str + i
            if i == '\"':
                quote = 0
        else:
            if i in '{[' :
                blank += 4
                new_str = new_str + i + '\n'
                for j in range(blank):
                    new_str = new_str + ' '
            elif i in '}]':
                blank -= 4
                if blank < 0:
                    raise ValueError('unpaired braces')
                new_str = new_str + '\n'
                for j in range(blank):
                    new_str = new_str + ' '
                new_str = new_str + i
            elif i == ',':
                new_str = new_str + i + '\n'
                for j in range(blank):
                    new_str = new_str + ' '
            elif i in '\n\t ':
                pass
            else:
                new_str = new_str + i
                if i == '\"':
                    quote = 1
        #print(new_str)
    if blank != 0:
        raise ValueError('unpaired braces')
    return new_str

if __name__ == '__main__':

    a='''
{"content":"每天饮水量2000ml左右，促进新陈代谢","id":440,"title":"多喝水","expertId":1,"img":""},
'''

    
    print(a)
    print('==============')
    a = format_json(a)
    print(a)
