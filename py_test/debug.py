from py_test.general import vic_method

a = vic_method.replace_special_value('${t|2000-10-1,,,,date}$')
print(a)
a = vic_method.replace_special_value('${t|2000-08-11 09:23:40,,second,3,S}$')
print(a)
# a = vic_method.replace_special_value('${t|2000-1-1 13:00:04.914,,,,f}$')
# a = vic_method.replace_special_value('${t|now,,Y,-1}$')

# print(a)