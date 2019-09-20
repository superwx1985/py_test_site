import logging
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.remote_connection import RemoteConnection


# 获取浏览器driver
def get_driver_(config, execute_str, logger=logging.getLogger('py_test')):
    dr = None
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'],)
        chrome_options.add_argument('start-maximized')
        # chrome_options._arguments = [
        #     'test-type',
        #     "start-maximized",
        #     "no-default-browser-check",
        #     "disable-infobars",
        # ]
        if config.ui_selenium_client == 1:  # 本地
            if config.ui_driver_type == 1:  # Chrome
                dr = webdriver.Chrome(options=chrome_options)
            elif config.ui_driver_type == 2:  # IE
                dr = webdriver.Ie()
            elif config.ui_driver_type == 3:  # FireFox
                if config.ui_driver_ff_profile:
                    dr = webdriver.Firefox(firefox_profile=webdriver.FirefoxProfile(config.ui_driver_ff_profile))
                else:
                    dr = webdriver.Firefox()
            elif config.ui_driver_type == 4:  # PhantomJS
                dr = webdriver.PhantomJS()
            else:
                raise ValueError('浏览器类型错误，请检查配置项')
        elif config.ui_selenium_client == 2:  # 远程
            if not config.ui_remote_ip or not config.ui_remote_port:
                raise ValueError('缺少远程驱动配置参数，检查配置项')
            if config.ui_driver_type == 1:  # Chrome
                dr = webdriver.Remote(
                    command_executor='http://{}:{}/wd/hub'.format(config.ui_remote_ip, config.ui_remote_port),
                    desired_capabilities=DesiredCapabilities.CHROME, options=chrome_options
                )
            elif config.ui_driver_type == 2:  # IE
                dr = webdriver.Remote(
                    command_executor='http://{}:{}/wd/hub'.format(config.ui_remote_ip, config.ui_remote_port),
                    desired_capabilities=DesiredCapabilities.INTERNETEXPLORER
                )
            elif config.ui_driver_type == 3:  # FireFox
                dr = webdriver.Remote(
                    command_executor='http://{}:{}/wd/hub'.format(config.ui_remote_ip, config.ui_remote_port),
                    desired_capabilities=DesiredCapabilities.FIREFOX
                )
            elif config.ui_driver_type == 4:  # PhantomJS
                dr = webdriver.Remote(
                    command_executor='http://{}:{}/wd/hub'.format(config.ui_remote_ip, config.ui_remote_port),
                    desired_capabilities=DesiredCapabilities.PHANTOMJS
                )
            else:
                raise ValueError('浏览器类型错误，请检查配置项')
        else:
            raise ValueError('驱动类型错误，请检查配置项')

        if config.ui_window_size == 2:
            if not config.ui_window_width or not config.ui_window_height:
                raise ValueError('自定义窗口但未指定大小，请检查配置项')
            dr.set_window_size(config.ui_window_width, config.ui_window_height)
            dr.set_window_position(config.ui_window_position_x or 0, config.ui_window_position_y or 0)
        else:
            dr.maximize_window()
    except Exception:
        try:
            if dr:
                dr.quit()
        except:
            logger.warning('【{}】\t有一个浏览器无法关闭，请手动关闭'.format(execute_str), exc_info=True)
        raise
    else:
        return dr


# 获取浏览器driver，添加重试功能
def get_driver(config, execute_str, retry=3, timeout=20, logger=logging.getLogger('py_test')):
    RemoteConnection.set_timeout(timeout)  # 设置RemoteConnection的初始timeout值
    for i in range(retry):
        try:
            dr = get_driver_(config, execute_str, logger)
            return dr
        except Exception as e:
            if i >= retry - 1:
                raise
            else:
                logger.warning('【{}】\t浏览器初始化出错，尝试进行第{}次初始化。错误信息 => {}'.format(execute_str, i+2, e))
                continue
