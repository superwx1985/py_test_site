

a = "update main_caseresult set step_result_id = '{}' where step_result_id = {};"

b = "update main_stepresult_imgs set image_id = '{}' where image_id = {};"

c = "update main_case set variable_group_id = '{}' where variable_group_id = {};"

d = "update main_variable set variable_group_id = '{}' where variable_group_id = {};"

e = "update main_image set id = '{}' where id = {};"


def get_new_id(id_):
    return '{:0>32}'.format(id_)


for i in range(1, 117):
    # print(a.format(get_new_id(i), i))
    print(b.format(get_new_id(i), i))
    # print(c.format(get_new_id(i), i))
    # print(d.format(get_new_id(i), i))
    print(e.format(get_new_id(i), i))

