import logging
from selenium.common import exceptions
from selenium.webdriver.remote.webelement import WebElement


class Variables:
    def __init__(self, logger=logging.getLogger('py_test')):
        self.variable_dict = dict()
        self.logger = logger

    @staticmethod
    def check_name(name):
        if name.find('${') != -1 or name.find('}$') != -1:
            raise ValueError('The variable name [' + name + '] is invalid, it should not have "${" or "}$"')

    # 设置变量
    def set_variable(self, name, value, msg_len=None):
        self.check_name(name)
        if msg_len and str(msg_len).isdigit() and len(str(value)) > msg_len:
            value_ = '{}【变量值过长，后续部分不再显示】'.format(str(value)[:msg_len])
        else:
            value_ = value
        if name in self.variable_dict:
            msg = '变量【{}】的值由【{}】变更为【{}】'.format(name, self.variable_dict[name], value_)
        else:
            msg = '变量【{}】被赋值为【{}】'.format(name, value_)
        self.variable_dict[name] = value
        self.logger.debug(msg)
        return msg

    # 获取变量
    def get_variable(self, name):
        variable_ = None
        found = False
        if name in self.variable_dict:
            found = True
            variable_ = self.variable_dict[name]
        return found, variable_


# 先获取局部变量，找不到则获取全局变量
def get_variable(name, variables=None, global_variables=None):
    variable_ = None
    found = False
    found_local = False
    found_global = False
    if isinstance(variables, Variables):
        found_local, variable_ = variables.get_variable(name)
    if not found_local:
        found_global, variable_ = global_variables.get_variable(name)
    if found_local:
        found = 'local'
    elif found_global:
        found = 'global'
    if not found:
        raise ValueError('找不到名为【{}】的变量'.format(name))
    return found, variable_


# 取变量的字符串
def get_str(name, variables=None, global_variables=None):
    found, variable_ = get_variable(name, variables, global_variables)
    if isinstance(variable_, list):
        str_ = name
    else:
        str_ = str(variable_)
    return str_


# 取变量的元素
def get_elements(name, variables=None, global_variables=None):
    found, variable_ = get_variable(name, variables, global_variables)
    if isinstance(variable_, WebElement):
        elements = [variable_]
    elif isinstance(variable_, list) and isinstance(variable_[0], WebElement):
        elements = variable_
    else:
        raise exceptions.NoSuchElementException('变量【{}】不是一个元素'.format(name))
    return elements


# 获取相关变量字典
def get_variable_dict(variables=None, global_variables=None):
    dict_ = dict()
    if isinstance(global_variables, Variables):
        dict_ = global_variables.variable_dict
    if isinstance(variables, Variables):
        local_dict_ = variables.variable_dict
        dict_ = {**dict_, **local_dict_}
    return dict_


