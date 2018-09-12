import logging


class PublicElements:
    def __init__(self, logger=logging.getLogger('py_test')):
        self.element_info_dict = dict()
        self.logger = logger

    def add_element_info(self, name, element_info):
        self.element_info_dict[name] = element_info

    def get_element_info(self, name):
        return self.element_info_dict[name]

