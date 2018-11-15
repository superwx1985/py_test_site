from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep


dr = webdriver.Chrome()
try:
    dr.get('http://192.192.185.140')
    sleep(2)
    dr.find_element_by_id('id_username').send_keys('vic')
    sleep(2)
    from py_test.ui_test.method import perform_special_action

    by = 'id'
    locator = 'id_username'
    data = '$CONTROL+a+$CONTROL+$BACKSPACE+tesT'
    timeout = 10
    index_ = None
    base_element = None
    special_action = 'send_keys_to_element'
    variables = None
    global_variables = None

    perform_special_action(dr, by, locator, data, timeout, index_, base_element, special_action, variables,
                           global_variables)

except:
    raise
finally:
    sleep(2)
    dr.quit()