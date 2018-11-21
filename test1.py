from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from selenium.webdriver.common.by import By


try:
    dr = webdriver.Chrome()
    dr.set_window_position(1920-1366, 0)
    dr.set_window_size(1366, 900)
    dr.get('http://192.192.190.33:8089/mine/mine/business/module/mineCenter/index.jsp#/')

    from py_test.ui_test import method


    timeout = 20
    index_ = None
    base_element = None
    data = ''

    method.try_to_enter(dr, By.ID, 'j_username', 'admin', timeout, index_)
    method.try_to_enter(dr, By.ID, 'j_password', '123', timeout, index_)
    method.try_to_click(dr, By.ID, 'loginId', timeout, index_)

    locator = '#processIndex > div.index_analysis_left.task.task-toggle > div > div.tab-pane.active > div.top > div > div > div.right > div > i.fa.fa-search.search_deep.index_search_kg'
    method.try_to_click(dr, By.CSS_SELECTOR, locator, timeout, index_)

    method.perform_special_action(dr, By.ID, 'input_search', 'autotest001+$ENTER', timeout, index_, 'send_keys_to_element')

    method.try_to_click(dr, By.CSS_SELECTOR, '#processCourse ul li:nth-of-type(1)', timeout, index_)

    print('【搜索节点】点击logo，使历程任务列表隐藏')
    method.try_to_click(dr, By.CSS_SELECTOR, '.user', timeout, index_)

    print('【搜索节点】点击“历程算子”打开资源列表')
    method.try_to_click(dr, By.XPATH, '//*[@id="anasidebar-div"]/div/ul/li[2]/p', timeout, index_)

    print('【搜索节点】点击“搜索”按钮')
    locator = '#anasidebar-div > div > div.navCont > div:nth-child(2)> div.navtit.clearfix > span > i.proRes-search-btn.index_search_kg.fa.fa-search'
    method.try_to_click(dr, By.CSS_SELECTOR, locator, timeout, index_)

    print('【搜索节点】输入框输入关键字')
    method.try_to_enter(dr, By.XPATH, '//*[@id="anasidebar-div"]/div/div[2]/div[2]/div[2]/input', 'rydz', timeout, index_)

    print('等待3秒')
    sleep(3)

    method.try_to_click(dr, By.CSS_SELECTOR, '#processIndex .search-res-content div[namevalue="人员地址表"]', timeout, index_)
    print('【拖拽节点】拖拽选中的节点')
    method.perform_special_action(dr, By.CSS_SELECTOR, '#processIndex .search-res-content div[namevalue="人员地址表"]', '', timeout, index_, 'click_and_hold')

    print('等待3秒')
    sleep(3)

    print('【拖拽节点】移动鼠标到画布中间')
    method.perform_special_action(dr, '', '', '500,100', timeout, index_, 'move_by_offset')
    # method.perform_special_action(dr, By.ID, 'container', '500,100', timeout, index_, 'move_to_element_with_offset')

    print('等待3秒')
    sleep(3)

    print('【拖拽节点】在目标位置释放鼠标')
    method.perform_special_action(dr, '', '', '', timeout, index_, 'release')

    # print('拖动xx')
    # method.perform_special_action(dr, By.CSS_SELECTOR, '#g_5707E800-613E-4D7A-99D6-A946123857DF', data, timeout, index_, 'click_and_hold')
    #
    # print('【拖拽节点】移动鼠标到画布中间')
    # method.perform_special_action(dr, '', '', '400,100', timeout, index_, 'move_by_offset')
    #
    # print('等待5秒')
    # sleep(5)
    #
    # print('【拖拽节点】在目标位置释放鼠标')
    # method.perform_special_action(dr, '', '', '', timeout, index_, 'release')
    #
    # method.perform_special_action(dr, By.ID, 'NodeD3798C1E-1776-4695-9464-D3DA508C5DB1', '', timeout, index_, 'click_and_hold')
    # method.perform_special_action(dr, By.ID, 'container', '400,100', timeout, index_, 'move_to_element_with_offset')
    #
    # method.perform_special_action(dr, By.CSS_SELECTOR, '#anasidebar-div > div > div.navCont >div:nth-of-type(6) > div:nth-of-type(1) > svg > use', '400,100', timeout, index_, 'drag_and_drop_by_offset')
    #
    # element = dr.find_element_by_css_selector('#anasidebar-div > div > div.navCont >div:nth-of-type(6) > div:nth-of-type(1) > svg > use')
    # target_element = dr.find_element_by_id('container')
    # ActionChains(dr).drag_and_drop(element, target_element).perform()

except:
    raise
else:
    print('END')
    sleep(10)
    print('dr quit')
    # dr.quit()
