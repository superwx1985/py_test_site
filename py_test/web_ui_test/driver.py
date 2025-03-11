import logging
import os
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.client_config import ClientConfig
import py_test_site.settings as settings


# 获取浏览器driver
def get_driver_(config, execute_str, timeout, logger=logging.getLogger('py_test')):
    dr = None
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("useAutomationExtension", False)  # 去掉开发者警告
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])  # 隐藏“正由自动化软件控制”提示，不打印driver日志
        chrome_options.add_experimental_option("prefs", {"credentials_enable_service": False, "profile.password_manager_enabled": False})  #禁用“保存密码”弹出窗口
        chrome_options.add_argument('start-maximized')  # 最大化
        chrome_options.add_argument("disable-cache")  # 禁用缓存

        if config.ui_selenium_client == 1:  # 本地
            if config.ui_driver_type == 1:  # Chrome
                chrome_options.binary_location = settings.CHROME_BINARY_LOCATION  # 指定chrome binary位置
                os.environ["webdriver.chrome.driver"] = settings.WEBDRIVER_CHROME_DRIVER  # 指定chrome driver位置
                dr = webdriver.Chrome(options=chrome_options)
            elif config.ui_driver_type == 2:  # IE
                dr = webdriver.Ie()
            elif config.ui_driver_type == 3:  # FireFox
                if config.ui_driver_ff_profile:
                    firefox_options = webdriver.FirefoxOptions()
                    firefox_options.profile = webdriver.FirefoxProfile(config.ui_driver_ff_profile)
                    dr = webdriver.Firefox(options=firefox_options)
                else:
                    dr = webdriver.Firefox()
            elif config.ui_driver_type == 4:  # Edge
                dr = webdriver.Edge()
            else:
                raise ValueError('浏览器类型错误，请检查配置项')
        elif config.ui_selenium_client == 2:  # 远程
            if not config.ui_remote_ip or not config.ui_remote_port:
                raise ValueError('缺少远程驱动配置参数，检查配置项')
            grid_server = f'{config.ui_remote_ip}:{config.ui_remote_port}'
            # 创建 ClientConfig 对象，设置超时
            client_config = ClientConfig(grid_server)
            client_config.timeout = timeout  # 设置请求超时
            if config.ui_driver_type == 1:  # Chrome
                # chrome_options.browser_version = '131.0.6778.69'
                dr = webdriver.Remote(
                    command_executor=grid_server,
                    options=chrome_options,
                    client_config=client_config
                )
            elif config.ui_driver_type == 2:  # IE
                dr = webdriver.Remote(
                    command_executor=grid_server,
                    options=webdriver.IeOptions(),
                    client_config=client_config
                )
            elif config.ui_driver_type == 3:  # FireFox
                dr = webdriver.Remote(
                    command_executor=grid_server,
                    options=webdriver.FirefoxOptions(),
                    client_config=client_config
                )
            elif config.ui_driver_type == 4:  # Edge
                dr = webdriver.Remote(
                    command_executor=grid_server,
                    options=webdriver.EdgeOptions(),
                    client_config=client_config
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
    for i in range(retry):
        try:
            dr = get_driver_(config, execute_str, timeout, logger)
            return dr
        except Exception as e:
            if i >= retry - 1:
                raise
            else:
                logger.warning('【{}】\t浏览器初始化出错，尝试进行第{}次初始化。错误信息 => {}'.format(execute_str, i+2, e))
                continue


if __name__ == '__main__':
    class Config:
        ui_selenium_client = 2
        ui_remote_ip = "10.100.1.234"
        ui_remote_port = "4444"
        ui_driver_type = 1
        ui_window_size = 1
        ui_window_width = 1024
        ui_window_height = 748
        ui_window_position_x = 0
        ui_window_position_y = 0
        ui_driver_ff_profile = ""

    conf = Config()
    get_driver_(conf, "debug")
