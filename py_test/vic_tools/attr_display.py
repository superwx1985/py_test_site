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
            _str = _str + _format.format(key, getattr(self, key)) + '\n'
        return _str

    def __str__(self):
        return "< {} - {} >\n{}".format(self.__class__.__name__, id(self), self.gather_attrs())
