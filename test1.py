import time
import uuid
import os
import logging
import datetime
from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
from py_test.vic_tools import vic_find_object, vic_eval
from py_test.vic_tools.vic_str_handle import change_string_to_digit
from py_test.general.thread_log import get_thread_logger

logger = logging.getLogger()


def get_special_keys(data_):
    data_ = data_.replace('\\+', '#{$plus}#')
    data_list = data_.split('+')
    keys = list()
    from selenium.webdriver.common.keys import Keys
    for key_str in data_list:
        key_str = key_str.replace('#{$plus}#', '+')
        if key_str.find('$') == 0 and len(key_str) > 1:
            try:
                key_str = getattr(Keys, key_str.replace('$', '', 1).upper())
            except AttributeError:
                logger.warning('【{}】不是一个合法的特殊键，不进行转换'.format(key_str))
            keys.append(key_str)
        else:
            keys.append(key_str)
    return keys

chrome_option = webdriver.ChromeOptions()
chrome_option._arguments = ['test-type', "start-maximized", "no-default-browser-check"]
dr = webdriver.Chrome(chrome_options=chrome_option)

dr.get('http://100.100.200.60:8080/msp/msp/sso/login.jsp?targetUrl=http%3A%2F%2F100.100.200.60%2Feip%2Fhome-page%2Findex.jsp')

elements = dr.find_elements('id', 'j_username')
element = elements[0]
element.clear()
element.send_keys('123456ab')

from selenium.webdriver.common.keys import Keys
data = '$control+ac+$BACKSPACE+v+v+$control+v\\+'
data = get_special_keys(data)
print(data)
ActionChains(dr).send_keys_to_element(element, data).perform()


