def find_x_in_json(x,json_):
    count = json_.count(x)
    value_list = []
    end_index = 0
    while (count):
        start_index = json_.find('"'+x+'":',end_index)
        end_index1 = json_.find('}',start_index+3+len(x))
        end_index2 = json_.find(',',start_index+3+len(x))
        end_index3 = json_.find('"',start_index+3+len(x))
        end_index4 = json_.find('"',end_index3+1) + 1
        print(start_index,end_index1,end_index2,end_index3)
        if (end_index1 < end_index2 or end_index2 == -1) and (end_index1 < end_index3 or end_index3 == -1) :
            end_index = end_index1
        elif end_index3 < end_index2:
            end_index = end_index4
        elif end_index2 < end_index3 or end_index3 == -1:
            end_index = end_index2
        elif end_index3 == -1:
            end_index = json_.find('"',end_index3+1) + 1
        else:
            raise ValueError('error format at %s' %json_[start_index:])
        value_list.append((json_[start_index+3+len(x):end_index]).replace(' ',''))
        count -= 1
    return value_list