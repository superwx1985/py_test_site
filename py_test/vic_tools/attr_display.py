import json

class AttrDisplay:
    """打印属性"""
    def gather_attrs(self):
        # return ", ".join("{}={}".format(k, getattr(self, k)) for k in self.__dict__.keys())
        _str = ''
        x = 1
        for key in self.__dict__:
            _x = len(key)
            if _x > x:
                x = _x
        _format = '{{:<{}}}\t=>\t{{}}'.format(x)
        keys = sorted(self.__dict__.keys())
        for key in keys:
            value = getattr(self, key)
            # 对列表进行特殊处理，防止打印出多余的反斜杠
            if isinstance(value, list):
                _value = "["
                # 遍历元素，逐个打印（用逗号分隔）
                for i, item in enumerate(value):
                    # 对字符串添加双引号，模拟目标格式
                    _value = f'{_value}"{item}"'
                    # 非最后一个元素，添加逗号和空格
                    if i != len(value) - 1:
                        _value = f"{_value}, "
                    else:
                        _value = f"{_value}]"
                value = _value
            _str = _str + _format.format(key, value) + '\n'
        return _str

    def __str__(self):
        return "< {} - {} >\n{}".format(self.__class__.__name__, id(self), self.gather_attrs())
