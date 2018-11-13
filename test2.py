import datetime, time, logging
from py_test.general.vic_method import replace_special_value

str = '${t|2018-09-26 09:28:15.956083,,,,yd}$'
a = replace_special_value('${{{}|{}}}$'.format('r', '50,100,2'), None, None, logger=logging.getLogger('debug'))
a = replace_special_value(str, None, None, logger=logging.getLogger('debug'))

print(a, type(a))


from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep


dr = webdriver.Chrome()
try:
    dr.get('http://127.0.0.1/case/146/?next=/cases/')
    sleep(2)
    dr.find_element_by_id('id_username').send_keys('vic')
    dr.find_element_by_id('id_password').send_keys('abcd123!')
    dr.find_element_by_id('login_button').click()
    sleep(3)
    # dr.find_element_by_css_selector('#m2m_selected_table table tbody tr[pk="537"] td[name] a').click()
    td = dr.find_element_by_css_selector('#m2m_selected_table table tbody tr[pk="537"] td[moveable]')
    ac = ActionChains(dr)
    # ac.click_and_hold(td).move_by_offset(0, 100).perform()
    ActionChains(dr).click_and_hold(td).perform()
    sleep(1)
    ActionChains(dr).move_by_offset(0, 100).perform()
    sleep(2)
except:
    raise
finally:
    dr.quit()