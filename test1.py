import uuid


a = "update main_stepresult set step_id = '000000000000000000000000000000{}' where step_id = {};"

b = "update main_casevsstep set step_id = '000000000000000000000000000000{}' where step_id = {};"

c = "update main_step set id = '000000000000000000000000000000{}' where id = {};"

for i in range(10, 100):
    print(a.format(i, i))
    print(b.format(i, i))
    print(c.format(i, i))