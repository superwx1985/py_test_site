from py_test.init_log import get_thread_logger


class ElementInfo:
    def __init__(self, by, locator):
        self.by = by
        self.locator = locator
        self.logger = get_thread_logger()


class PublicElements:
    def __init__(self):
        self.element_info_dict = dict()
        self.logger = get_thread_logger()

    def add_element_info(self, name, element_info):
        self.element_info_dict[name] = element_info

    def get_element_info(self, name):
        return self.element_info_dict[name]


# 公共元素组容器
public_elements = PublicElements()
