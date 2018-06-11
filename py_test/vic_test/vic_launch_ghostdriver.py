'''
Created on 2015年3月25日

@author: wangx4
'''
# -*- coding: utf-8 -*-
from selenium import webdriver

dr = webdriver.PhantomJS('phantomjs')
dr.maximize_window()
dr.get('http://www.baidu.com')
print(dr.title)
print(dr.current_url)
dr.get_screenshot_as_file('./baidu.png')
dr.quit()