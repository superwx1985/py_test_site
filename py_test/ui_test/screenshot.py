import time
import uuid
import os
import io
import datetime
import logging
from selenium.common import exceptions
from PIL import Image
from django.core.files.uploadedfile import UploadedFile
from py_test.ui_test import method


def get_screenshot(vic_step):
    element = None
    img = None
    run_result = None
    if vic_step.ui_by and vic_step.ui_locator:
        _ui_data = vic_step.ui_data  # 把ui_data置空，防止查找元素时被当做数量限制表达式
        vic_step.ui_data = None
        run_result_temp, visible_elements, _ = method.wait_for_element_visible(vic_step)
        vic_step.ui_data = _ui_data
        if visible_elements:
            element = visible_elements[0]
        else:
            run_result = ['f', '截图失败，指定的截取元素未找到，{}'.format(run_result_temp[1])]
    if not run_result:
        try:
            run_result, img = _get_screenshot(vic_step.dr, element)
        except Exception as e:
            run_result = ['f', '截图失败，原因为{}'.format(getattr(e, 'msg', str(e)))]
    return run_result, img


# 根据浏览器类型调取不同的截图方法
def _get_screenshot(dr, element=None):
    bio = io.BytesIO()
    # 刚打开某个页面时截图会报错，加入3次重试机制
    for i in range(3):
        try:
            if element:
                img = get_image_on_element(dr, element)
            else:
                if 'chrome' == dr.name:
                    img = get_long_screenshot_img_for_chrome(dr)
                else:
                    img = Image.open(io.BytesIO(dr.get_screenshot_as_png()))
        except exceptions.WebDriverException as e:
            if 'unknown error: cannot take screenshot' in e.msg:
                time.sleep(1)
                continue
            else:
                raise
        else:
            img.save(bio, format='png')
            break

    name = datetime.datetime.now().strftime('%Y%m%d_%H%M%S.png')
    from main.models import Image as db_Image
    image = db_Image(name=name, img=UploadedFile(bio, name=name))
    image.save()
    bio.close()
    run_result = ['p', '截图成功【{}】'.format(name)]
    return run_result, image


# chrome截长图
def get_long_screenshot_img_for_chrome(dr, scroll_step=100, scroll_delay=0.1, start_height=0, max_height=10000):
    if start_height >= max_height:
        raise ValueError("截图开始高度大于最大高度")
    window_top = dr.execute_script('return scrollY;')
    if start_height != window_top:
        scroll_to_height(dr, start_height, scroll_step, scroll_delay)  # 滚动到开始高度
    window_height = dr.execute_script('return window.innerHeight;')  # 窗口高度
    time.sleep(scroll_delay)
    body_height = dr.execute_script('return document.body.scrollHeight;')  # 网页高度
    img_height = body_height - start_height  # 需要截取的高度
    if window_height <= 0 or img_height <= 0:
        raise ValueError("截图高度小于0")
    if max_height < window_height:
        max_height = window_height
    if img_height > max_height:
        img_height = max_height
    count = int((img_height / window_height))
    img1 = Image.open(io.BytesIO(dr.get_screenshot_as_png()))
    for i in range(1, count):
        scroll_to_height(dr, start_height + window_height * i, scroll_step, scroll_delay)
        img2 = Image.open(io.BytesIO(dr.get_screenshot_as_png()))
        img1 = vertical_join_image(img1, img2)
        del img2
    window_top = dr.execute_script('return scrollY;')  # 获取当前窗口位置
    if window_top < body_height - window_height:
        window_top_old = window_top
        scroll_to_height(dr, body_height - window_height, scroll_step, scroll_delay)
        window_top = dr.execute_script('return scrollY;')
        img2 = Image.open(io.BytesIO(dr.get_screenshot_as_png()))
        window_top_delta = window_top - window_top_old
        left = 0
        top = img2.size[1] - window_top_delta
        right = img2.size[0]
        bottom = img2.size[1]
        img2 = img2.crop((left, top, right, bottom))  # defines crop points
        img1 = vertical_join_image(img1, img2)
        del img2
    return img1


# 垂直合并图片
def vertical_join_image(img1, img2):
    width1 = img1.size[0]
    height1 = img1.size[1]
    width2 = img2.size[0]
    height2 = img2.size[1]
    if width1 >= width2:
        width3 = width1
    else:
        width3 = width2
    img3 = Image.new('RGB', (width3, height1 + height2))
    img3.paste(img1, (0, 0, width1, height1))
    img3.paste(img2, (0, height1, width2, height1 + height2))
    return img3


# 只截取某个元素
def get_image_on_element(dr, element):
    window_top = dr.execute_script('return scrollY;')
    dr.execute_script("arguments[0].scrollIntoView();", element)
    time.sleep(1)
    window_top_new = dr.execute_script('return scrollY;')
    scroll_height = window_top_new - window_top
    left = element.location['x']
    right = left + element.size['width']
    top = element.location['y'] - scroll_height
    bottom = top + element.size['height']

    if 'chrome' == dr.name:
        img = get_long_screenshot_img_for_chrome(dr, 100, 0.1, scroll_height, scroll_height + element.size['height'])
    else:
        img = Image.open(io.BytesIO(dr.get_screenshot_as_png()))
    # 裁剪图片
    img.crop((left, top, right, bottom))
    return img


# 下拉加载更多内容
def scroll_down_for_loading(driver, wait_time=30, print_=True, logger=logging.getLogger('py_test')):
    # driver.execute_script("arguments[0].scrollIntoView();")
    driver.execute_script("""
        (function () {
            var y = scrollY;
            var step = 100;
            window.scroll(0, 0);

            function f() {
                if (y < document.body.scrollHeight) {
                    y += step;
                    window.scroll(0, y);
                    setTimeout(f, 100);
                } else {
                    window.scroll(0,0);
                    document.title += "scroll-done";
                }
            }

            setTimeout(f, 1000);
        })();
    """)

    start_time = time.time()
    for i in range(wait_time):
        if "scroll-done" in driver.title:
            return
        time.sleep(1)
        if print_:
            logger.info('经过%s秒 - 向下拖动第%s次' % (str(round(time.time() - start_time, 2)), i))


# 滚动到顶部
def scroll_to_height(dr, _to, _step, delay):
    _from = dr.execute_script('return scrollY')
    count = int((_to - _from) / _step)
    if count >= 0:
        for i in range(1, count + 1):
            dr.execute_script('window.scroll(0, arguments[0]);', _from + _step * i)
            time.sleep(delay)
    else:
        count = abs(count)
        for i in range(1, count + 1):
            dr.execute_script('window.scroll(0, arguments[0]);', _from - _step * i)
            time.sleep(delay)
    top = dr.execute_script('return scrollY')
    if top != _to:
        dr.execute_script('window.scroll(0, arguments[0]);', _to)
        time.sleep(delay)
    return count


# 生成截图路径
def get_screenshot_full_name(file_name, base_path=os.getcwd(), logger=logging.getLogger('py_test')):
    _name_list = os.path.splitext(file_name)
    from py_test.general.vic_method import check_name
    _name_result = check_name(_name_list[0])
    if _name_result[0]:
        file_name = _name_list[0] + '.png'
    else:
        logger.warning(_name_result[1])
        file_name = 'screenshot_{}.png'.format(uuid.uuid1())
        # file_name = 'screenshot_' + datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f") + '.png'
    return os.path.join(base_path, file_name)
