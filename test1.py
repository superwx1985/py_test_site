from py_test.ui_test import method
from selenium.webdriver.common.by import By

dr = None


print('start', dr.current_url)
method.try_to_click(dr, By.XPATH, '//div[@id="tablist"]//span[text()="案件已办公文"]', 20, None)
method.try_to_switch_to_frame(dr, By.ID, 'archiveKindCode--caseHandleArchive_iframe', 20, None)
print('switch', dr.current_url)
method.wait_for_element_visible(dr, By.XPATH, '//tr[td[@title="案件受理登记表"] and td[@title="已结束"]]', 20)
print('end', dr.current_url)
