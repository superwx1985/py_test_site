from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from py_test.vic_tools.vic_date_handle import get_timedelta_str

result_state_list = (
    (0, '跳过'),
    (1, '成功'),
    (2, '失败'),
    (3, '异常'),
    (4, '中止'),
)

error_handle_list_ = (
    (0, '', None),
    (1, '中止测试', 'stop'),
    (2, '继续测试', 'continue'),
    (3, '暂停测试', 'pause'),
    (4, '跳过步骤', 'skip'),
)
error_handle_dict = {i[0]: i[2] for i in error_handle_list_}
error_handle_list = [(i[0], i[1]) for i in error_handle_list_]
error_handle_list_suite = error_handle_list[1:]


# 套件表
class Suite(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    project = models.ForeignKey('main.Project', on_delete=models.SET_NULL, blank=True, null=True)
    creator = models.ForeignKey(
        User, verbose_name='创建人', related_name='suite_creator', on_delete=models.SET_NULL, blank=True, null=True)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(
        User, verbose_name='修改人', related_name='suite_modifier', on_delete=models.SET_NULL, blank=True, null=True)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    timeout = models.FloatField(default=10)
    ui_step_interval = models.FloatField(default=0)
    ui_get_ss = models.BooleanField(default=True)
    log_level_list = (
        (1, 'DEV'),
        (10, 'DEBUG'),
        (20, 'INFO'),
        (30, 'WARNING'),
        (40, 'ERROR'),
        (50, 'CRITICAL'),
    )
    log_level = models.IntegerField(choices=log_level_list, default=20)
    thread_count = models.IntegerField(default=1)
    config = models.ForeignKey('main.Config', on_delete=models.SET_NULL, blank=True, null=True)
    variable_group = models.ForeignKey('main.VariableGroup', on_delete=models.SET_NULL, blank=True, null=True)
    element_group = models.ForeignKey('main.ElementGroup', on_delete=models.SET_NULL, blank=True, null=True)
    error_handle = models.IntegerField(choices=error_handle_list_suite, default=1)

    case = models.ManyToManyField('Case', through='SuiteVsCase', through_fields=('suite', 'case'))

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    class Meta:
        ordering = ['-modified_date']

    def __str__(self):
        return self.name


# 用例表
class Case(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    project = models.ForeignKey('main.Project', on_delete=models.SET_NULL, blank=True, null=True)
    creator = models.ForeignKey(
        User, verbose_name='创建人', related_name='case_creator', on_delete=models.SET_NULL, blank=True, null=True)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(
        User, verbose_name='修改人', related_name='case_modifier', on_delete=models.SET_NULL, blank=True, null=True)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    timeout = models.FloatField(blank=True, null=True)
    ui_step_interval = models.FloatField(blank=True, null=True)
    config = models.ForeignKey('main.Config', on_delete=models.SET_NULL, blank=True, null=True)
    variable_group = models.ForeignKey('main.VariableGroup', on_delete=models.SET_NULL, blank=True, null=True)
    error_handle = models.IntegerField(choices=error_handle_list, default=0)

    step = models.ManyToManyField('Step', through='CaseVsStep', through_fields=('case', 'step'))

    class Meta:
        # db_table = 'test_case_step'
        ordering = ['-modified_date']  # 这个字段是告诉Django模型对象返回的记录结果集是按照哪个字段排序的,-xxx表示降序，?xxx表示随机

    def __str__(self):
        return self.name


# 步骤表
class Step(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    project = models.ForeignKey('main.Project', on_delete=models.SET_NULL, blank=True, null=True)
    creator = models.ForeignKey(
        User, verbose_name='创建人', related_name='step_creator', on_delete=models.SET_NULL, blank=True, null=True)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(
        User, verbose_name='修改人', related_name='step_modifier', on_delete=models.SET_NULL, blank=True, null=True)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    action = models.ForeignKey('main.Action', on_delete=models.SET_NULL, blank=True, null=True)
    timeout = models.FloatField(blank=True, null=True)
    ui_step_interval = models.FloatField(blank=True, null=True)
    error_handle = models.IntegerField(choices=error_handle_list, default=0)
    save_as = models.CharField(blank=True, max_length=100)
    ui_by_list = (
        (0, ''),
        (1, 'id'),
        (2, 'xpath'),
        (3, 'link text'),
        (4, 'partial link text'),
        (5, 'name'),
        (6, 'tag name'),
        (7, 'class name'),
        (8, 'css selector'),
        (9, 'public element'),
        (10, 'variable'),
    )
    ui_by_dict = {i[0]: i[1] for i in ui_by_list}
    ui_by = models.IntegerField(choices=ui_by_list, default=0)
    ui_locator = models.TextField(blank=True)
    ui_index = models.IntegerField(blank=True, null=True)
    ui_base_element = models.CharField(max_length=1000, blank=True)
    ui_data = models.TextField(blank=True)
    ui_special_action_list_ = (
        (0, '', ''),
        (1, '鼠标 - 单击', 'click'),
        (2, '鼠标 - 点击后不放', 'click_and_hold'),
        (3, '鼠标 - 右键单击', 'context_click'),
        (4, '鼠标 - 双击', 'double_click'),
        (5, '鼠标 - 释放', 'release'),
        (6, '鼠标 - 移动到偏移点位置', 'move_by_offset'),
        (7, '鼠标 - 移动到某元素中间', 'move_to_element'),
        (8, '鼠标 - 移动到某元素左上角为基准的偏移点位置', 'move_to_element_with_offset'),
        (9, '鼠标 - 拖动某元素到另一元素上', 'drag_and_drop'),
        (10, '鼠标 - 拖动某元素到偏移点位置', 'drag_and_drop_by_offset'),
        (11, '键盘 - 按下某键不释放', 'key_down'),
        (12, '键盘 - 释放某键', 'key_up'),
        (13, '键盘 - 发送按键（组）到当前焦点元素', 'send_keys'),
        (14, '键盘 - 发送按键（组）到指定元素', 'send_keys_to_element'),
    )
    ui_special_action_dict = {i[0]: i[2] for i in ui_special_action_list_}
    ui_special_action_list = [(i[0], i[1]) for i in ui_special_action_list_]
    ui_special_action = models.IntegerField(choices=ui_special_action_list, default=0)
    ui_alert_handle_list_ = (
        (1, '确定', 'accept'),
        (2, '取消', 'dismiss'),
    )
    ui_alert_handle_dict = {i[0]: i[2] for i in ui_alert_handle_list_}
    ui_alert_handle_list = [(i[0], i[1]) for i in ui_alert_handle_list_]
    ui_alert_handle = models.IntegerField(choices=ui_alert_handle_list, default=1)
    ui_alert_handle_text = models.TextField(blank=True)
    api_url = models.TextField(blank=True)
    api_method_list = (
        (1, 'GET'),
        (2, 'HEAD'),
        (3, 'POST'),
        (4, 'PUT'),
        (5, 'PATCH'),
        (6, 'DELETE'),
        (7, 'OPTIONS'),
        (8, 'TRACE'),
    )
    api_method_dict = {i[0]: i[1] for i in api_method_list}
    api_method = models.IntegerField(choices=api_method_list, default=1)
    api_headers = models.TextField(blank=True)
    api_body = models.TextField(blank=True)
    api_decode = models.CharField(max_length=255, blank=True)
    api_data = models.TextField(blank=True)
    api_save = models.TextField(blank=True)
    other_data = models.TextField(blank=True)
    other_sub_case = models.ForeignKey(
        'main.Case', on_delete=models.SET_NULL, blank=True, null=True, related_name='step_sub_case')
    db_type_list_ = (
        (1, 'Oracle', 'oracle'),
        (2, 'MySQL', 'mysql'),
    )
    db_type_dict = {i[0]: i[2] for i in db_type_list_}
    db_type_list = [(i[0], i[1]) for i in db_type_list_]
    db_type = models.IntegerField(choices=db_type_list, default=1)
    db_host = models.CharField(max_length=255, blank=True)
    db_port = models.CharField(max_length=255, blank=True)
    db_name = models.CharField(max_length=255, blank=True)
    db_user = models.CharField(max_length=255, blank=True)
    db_password = models.CharField(max_length=255, blank=True)
    db_lang = models.CharField(max_length=255, blank=True)
    db_sql = models.TextField(blank=True)
    db_data = models.TextField(blank=True)

    class Meta:
        # db_table = 'test_case_step'
        ordering = ['-modified_date']

    def __str__(self):
        return self.name


# 套件和用例的对应关系
class SuiteVsCase(models.Model):
    suite = models.ForeignKey('main.Suite', on_delete=models.CASCADE)
    case = models.ForeignKey('main.Case', on_delete=models.CASCADE)
    creator = models.ForeignKey(
        User, verbose_name='创建人', related_name='suite_vs_case_creator', on_delete=models.SET_NULL, blank=True,
        null=True)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(
        User, verbose_name='修改人', related_name='suite_vs_case_modifier', on_delete=models.SET_NULL, blank=True,
        null=True)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        unique_together = ('suite', 'case', 'order')
        ordering = ['-modified_date']

    def __str__(self):
        return '{} [{}]<===>{} [{}]'.format(self.suite.id, self.suite.name, self.case.id, self.case.name)


# 用例和步骤关系表
class CaseVsStep(models.Model):
    case = models.ForeignKey('main.Case', on_delete=models.CASCADE)
    step = models.ForeignKey('main.Step', on_delete=models.CASCADE)
    creator = models.ForeignKey(
        User, verbose_name='创建人', related_name='case_vs_step_creator', on_delete=models.SET_NULL, blank=True,
        null=True)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(
        User, verbose_name='修改人', related_name='case_vs_step_modifier', on_delete=models.SET_NULL, blank=True,
        null=True)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        unique_together = ('case', 'step', 'order')
        ordering = ['-modified_date']

    # def case_id(self):
    #     return self.case.id
    #
    # def step_id(self):
    #     return self.step.id

    def __str__(self):
        return '{} [{}]<===>{} [{}]'.format(self.case.id, self.case.name, self.step.id, self.step.name)


# 动作表
class Action(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    creator = models.ForeignKey(
        User, verbose_name='创建人', related_name='action_creator', on_delete=models.SET_NULL, blank=True, null=True)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(
        User, verbose_name='修改人', related_name='action_modifier', on_delete=models.SET_NULL, blank=True, null=True)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    type = models.ForeignKey('main.ActionType', on_delete=models.SET_NULL, blank=True, null=True)
    order = models.FloatField(default=0)

    class Meta:
        unique_together = ('name', 'type')
        ordering = ['type', 'order']

    @property
    def full_name(self):
        return '{}-{}'.format(self.type, self.name)

    def __str__(self):
        return self.full_name

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.full_name


# 步骤类型字典表
class ActionType(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    def __str__(self):
        return self.name


# 配置表
class Config(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    creator = models.ForeignKey(
        User, verbose_name='创建人', related_name='config_creator', on_delete=models.SET_NULL, blank=True, null=True)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(
        User, verbose_name='修改人', related_name='config_modifier', on_delete=models.SET_NULL, blank=True, null=True)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    ui_selenium_client_list = (
        (0, '不启用'),
        (1, 'Selenium - 服务器本地浏览器'),
        (2, 'Selenium - 远程浏览器'),
    )
    ui_selenium_client = models.IntegerField(choices=ui_selenium_client_list, default=0)
    ui_remote_ip = models.CharField(max_length=100, blank=True)
    ui_remote_port = models.IntegerField(blank=True, null=True)
    ui_driver_list = (
        (1, 'Chrome'),
        (2, 'IE'),
        (3, 'FireFox'),
        (4, 'PhantomJS'),
    )
    ui_driver_type = models.IntegerField(choices=ui_driver_list, default=1)
    ui_window_size_list = (
        (1, '最大化'),
        (2, '自定义'),
    )
    ui_window_size = models.IntegerField(choices=ui_window_size_list, default=1)
    ui_window_width = models.IntegerField(blank=True, null=True)
    ui_window_height = models.IntegerField(blank=True, null=True)
    ui_window_position_x = models.IntegerField(blank=True, null=True)
    ui_window_position_y = models.IntegerField(blank=True, null=True)
    ui_driver_ff_profile = models.CharField(max_length=100, blank=True)

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    class Meta:
        ordering = ['-modified_date']

    def __str__(self):
        return self.name


# 变量组表
class VariableGroup(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    project = models.ForeignKey('main.Project', on_delete=models.SET_NULL, blank=True, null=True)
    creator = models.ForeignKey(
        User, verbose_name='创建人', related_name='variable_group_creator', on_delete=models.SET_NULL, blank=True,
        null=True)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(
        User, verbose_name='修改人', related_name='variable_group_modifier', on_delete=models.SET_NULL, blank=True,
        null=True)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    class Meta:
        ordering = ['-modified_date']

    def __str__(self):
        return self.name


# 变量表
class Variable(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    value = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    variable_group = models.ForeignKey('main.VariableGroup', on_delete=models.CASCADE)

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'variable_group')


# 元素组表
class ElementGroup(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    project = models.ForeignKey('main.Project', on_delete=models.SET_NULL, blank=True, null=True)
    creator = models.ForeignKey(
        User, verbose_name='创建人', related_name='element_group_creator', on_delete=models.SET_NULL, blank=True,
        null=True)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(
        User, verbose_name='修改人', related_name='element_group_modifier', on_delete=models.SET_NULL, blank=True,
        null=True)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    class Meta:
        ordering = ['-modified_date']

    def __str__(self):
        return self.name


# 元素表
class Element(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    by = models.IntegerField(choices=Step.ui_by_list, default=0)
    locator = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    element_group = models.ForeignKey('main.ElementGroup', on_delete=models.CASCADE)

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'element_group')


# suite测试结果
class SuiteResult(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    project = models.ForeignKey('main.Project', on_delete=models.SET_NULL, blank=True, null=True)
    creator = models.ForeignKey(
        User, verbose_name='创建人', related_name='suite_result_creator', on_delete=models.SET_NULL, blank=True,
        null=True)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(
        User, verbose_name='修改人', related_name='suite_result_modifier', on_delete=models.SET_NULL, blank=True,
        null=True)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)

    timeout = models.FloatField(blank=True, null=True)
    ui_step_interval = models.FloatField(blank=True, null=True)
    ui_get_ss = models.NullBooleanField(blank=True, null=True)
    log_level = models.IntegerField(blank=True, null=True)
    thread_count = models.IntegerField(blank=True, null=True)
    config = models.TextField(blank=True, null=True)
    variable_group = models.TextField(blank=True, null=True)
    element_group = models.TextField(blank=True, null=True)
    suite = models.ForeignKey('main.Suite', on_delete=models.SET_NULL, null=True, blank=True)

    start_date = models.DateTimeField(verbose_name='开始时间', blank=True, null=True)
    end_date = models.DateTimeField(verbose_name='结束时间', blank=True, null=True)
    execute_count = models.IntegerField(blank=True, null=True)
    pass_count = models.IntegerField(blank=True, null=True)
    fail_count = models.IntegerField(blank=True, null=True)
    error_count = models.IntegerField(blank=True, null=True)
    stop_count = models.IntegerField(blank=True, null=True)

    result_state = models.IntegerField(choices=result_state_list, blank=True, null=True)
    result_message = models.TextField(blank=True)
    result_error = models.TextField(blank=True)

    @property
    def elapsed_time(self):
        if self.end_date is None or self.start_date is None:
            return None
        else:
            return self.end_date - self.start_date

    @property
    def elapsed_time_str(self):
        if self.elapsed_time is None:
            return 'N/A'
        else:
            return get_timedelta_str(self.elapsed_time, 1)

    class Meta:
        ordering = ['-modified_date']


# case测试结果
class CaseResult(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)

    timeout = models.FloatField(blank=True, null=True)
    ui_step_interval = models.FloatField(blank=True, null=True)
    config = models.TextField(blank=True, null=True)
    variable_group = models.TextField(blank=True, null=True)

    suite_result = models.ForeignKey('main.SuiteResult', on_delete=models.CASCADE)
    step_result = models.ForeignKey('main.StepResult', on_delete=models.CASCADE, null=True, blank=True)
    parent_case_pk_list = models.TextField(blank=True, null=True)
    case = models.ForeignKey('main.Case', on_delete=models.SET_NULL, null=True, blank=True)
    case_order = models.IntegerField(blank=True, null=True)
    creator = models.ForeignKey(User, verbose_name='创建人', on_delete=models.SET_NULL, blank=True, null=True)
    start_date = models.DateTimeField(verbose_name='开始时间', blank=True, null=True)
    end_date = models.DateTimeField(verbose_name='结束时间', blank=True, null=True)
    execute_count = models.IntegerField(blank=True, null=True)
    pass_count = models.IntegerField(blank=True, null=True)
    fail_count = models.IntegerField(blank=True, null=True)
    error_count = models.IntegerField(blank=True, null=True)

    result_state = models.IntegerField(choices=result_state_list, blank=True, null=True)
    result_message = models.TextField(blank=True)
    result_error = models.TextField(blank=True)

    @property
    def elapsed_time(self):
        if self.end_date is None or self.start_date is None:
            return None
        else:
            return self.end_date - self.start_date

    @property
    def elapsed_time_str(self):
        if self.elapsed_time is None:
            return 'N/A'
        else:
            return get_timedelta_str(self.elapsed_time, 1)


# step测试结果
class StepResult(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    action = models.CharField(blank=True, max_length=100)

    case_result = models.ForeignKey('main.CaseResult', on_delete=models.CASCADE)
    step = models.ForeignKey('main.Step', on_delete=models.SET_NULL, null=True, blank=True)
    step_order = models.IntegerField(blank=True, null=True)
    loop_id = models.CharField(blank=True, max_length=100)

    creator = models.ForeignKey(User, verbose_name='创建人', on_delete=models.SET_NULL, blank=True, null=True)
    start_date = models.DateTimeField(verbose_name='开始时间', blank=True, null=True)
    end_date = models.DateTimeField(verbose_name='结束时间', blank=True, null=True)
    
    result_state = models.IntegerField(choices=result_state_list, blank=True, null=True)
    result_message = models.TextField(blank=True)
    result_error = models.TextField(blank=True)

    snapshot = models.TextField(blank=True, null=True)
    has_sub_case = models.BooleanField(default=False)

    ui_last_url = models.TextField(blank=True)
    imgs = models.ManyToManyField(to='Image')

    @property
    def elapsed_time(self):
        if self.end_date is None or self.start_date is None:
            return None
        else:
            return self.end_date - self.start_date

    @property
    def elapsed_time_str(self):
        if self.elapsed_time is None:
            return 'N/A'
        else:
            return get_timedelta_str(self.elapsed_time, 1)

    class Meta:
        ordering = ['pk']


class Image(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    img = models.ImageField(upload_to='img')


class Project(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    order = models.FloatField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Token(models.Model):
    uuid = models.UUIDField(auto_created=True, default=uuid.uuid1, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    is_active = models.BooleanField(default=True)
    value = models.CharField(verbose_name='token值', max_length=100)
    expire_date = models.DateTimeField(verbose_name='有效期', blank=True, null=True, default=timezone.now)
    user = models.ForeignKey(User, verbose_name='对应用户', on_delete=models.SET_NULL, blank=True, null=True)

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('value',)
