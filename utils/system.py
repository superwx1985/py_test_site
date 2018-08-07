# 获取当前函数名称
def get_current_function_name():
    import inspect
    return inspect.stack()[1][3]


# 通过函数名称获取函数
def get_function_with_name(space, name):
    # space = sys.modules[__name__]
    return getattr(space, name)


# 强制停止列表
FORCE_STOP = dict()
