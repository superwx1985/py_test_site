import logging
# from concurrent.futures import ThreadPoolExecutor, wait
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.remote_connection import RemoteConnection


# 获取浏览器driver
def get_driver_(config, logger=logging.getLogger('py_test')):
    dr = None
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options._arguments = [
            'test-type',
            "start-maximized",
            "no-default-browser-check",
            # "disable-browser-side-navigation",
        ]
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
        except Exception as e:
            logger.error('有一个浏览器驱动无法关闭，请手动关闭。错误信息 => {}'.format(e))
        raise
    else:
        return dr


# 获取浏览器driver，添加重试功能
def get_driver(config, retry=3, timeout=10, logger=logging.getLogger('py_test')):
    RemoteConnection.set_timeout(timeout)
    for i in range(retry):
        # pool = ThreadPoolExecutor(1)
        # futures = list()
        # futures.append(pool.submit(get_driver_, config=config, timeout=timeout, logger=logger))
        # # t = threading.Thread(target=get_driver_, args=(config, logger), daemon=True)
        # future_results = wait(futures, timeout=timeout+5, return_when='FIRST_EXCEPTION')
        # if len(future_results.done) == 0:
        #     logger.error('有一个浏览器驱动初始化超时，请手动关闭。')
        #     continue
        # for future_result in future_results.done:
        #     try:
        #         dr = future_result.result()
        #     except Exception as e:
        #         if i >= retry - 1:
        #             raise
        #         else:
        #             logger.warning('driver初始化出错，尝试重启driver。错误信息 => {}'.format(e))
        #             continue
        #     else:
        #         return dr
        try:
            dr = get_driver_(config, logger)
        except Exception as e:
            if i >= retry - 1:
                raise
            else:
                logger.warning('driver初始化出错，尝试重启driver。错误信息 => {}'.format(e))
                continue
        else:
            return dr