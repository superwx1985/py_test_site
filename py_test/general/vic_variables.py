from selenium.common import exceptions
from selenium.webdriver.remote.webelement import WebElement
from py_test.general.thread_log import get_thread_logger


class Variables:
    def __init__(self):
        self.variable_dict = dict()
        self.logger = get_thread_logger()

    @staticmethod
    def check_name(name):
        if name.find('${') != -1 or name.find('}$') != -1:
            raise ValueError('The variable name [' + name + '] is invalid, it should not have "${" or "}$"')

    # 设置变量
    def set_variable(self, name, value):
        self.check_name(name)
        if name in self.variable_dict:
            msg = '变量【{}】的值由【{}】变更为【{}】'.format(name, self.variable_dict[name], value)
        else:
            msg = '【{}】保存为变量【{}】'.format(value, name)
        self.logger.debug(msg)
        self.variable_dict[name] = value
        return msg

    # 获取变量
    def get_variable(self, name):
        variable_ = None
        found = False
        if name in self.variable_dict:
            found = True
            variable_ = self.variable_dict[name]
        return found, variable_


# 初始化全局变量
global_variables = Variables()


# 先获取局部变量，找不到则获取全局变量
def get_variable(name, variables=None):
    variable_ = None
    found = False
    if isinstance(variables, Variables):
        found, variable_ = variables.get_variable(name)
    if not found:
        found, variable_ = global_variables.get_variable(name)
    if not found:
        raise ValueError('没找到名为【{}】的变量'.format(name))
    return found, variable_


# 取变量的字符串
def get_str(name, variables=None):
    found, variable_ = get_variable(name, variables)
    if isinstance(variable_, list):
        str_ = name
    else:
        str_ = str(variable_)
    return str_


# 取变量的元素
def get_elements(name, variables=None):
    found, variable_ = get_variable(name, variables)
    if isinstance(variable_, WebElement):
        elements = [variable_]
    elif isinstance(variable_, list) and isinstance(variable_[0], WebElement):
        elements = variable_
    else:
        raise exceptions.NoSuchElementException('变量【{}】不是一个元素'.format(name))
    return elements


# 获取相关变量字典
def get_variable_dict(variables=None):
    dict_ = global_variables.variable_dict
    if isinstance(variables, Variables):
        local_dict_ = variables.variable_dict
        dict_ = {**dict_, **local_dict_}
    return dict_


