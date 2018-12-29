from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from selenium.webdriver.common.by import By
from py_test.ui_test import method


timeout = 20
index_ = None
base_element = None
data = ''

dr = webdriver.Chrome()
dr.set_window_position(1920-1366, 0)
dr.set_window_size(1366, 900)
dr.get('http://192.192.185.140/result/1273/?next=/results/')

dr.execute_script('''$('#onZoom').attr('style', 'display:block');''')

print('END')
sleep(10)
# dr.quit()
