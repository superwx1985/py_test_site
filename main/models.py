from django.db import models
from django.contrib.auth.models import User


# 用例表
class Case(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='case_creator', on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='case_modifier', on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    variable_group = models.ForeignKey('main.VariableGroup', on_delete=models.DO_NOTHING, blank=True, null=True)
    step = models.ManyToManyField('Step', through='CaseVsStep', through_fields=('case', 'step'))

    class Meta:
        pass
        # db_table = 'test_case_step'
        ordering = ['-pk']  # 这个字段是告诉Django模型对象返回的记录结果集是按照哪个字段排序的,-xxx表示降序，?xxx表示随机

    def __str__(self):
        return self.name


# 步骤表
class Step(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='step_creator', on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='step_modifier', on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    action = models.ForeignKey('main.Action', on_delete=models.DO_NOTHING)
    timeout = models.FloatField(blank=True, null=True)
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
    ui_by = models.IntegerField(choices=ui_by_list, default=0)
    ui_locator = models.TextField(blank=True)
    ui_index = models.IntegerField(blank=True, null=True)
    ui_base_element = models.TextField(blank=True)
    ui_data = models.TextField(blank=True)
    ui_special_action_list = (
        (0, ''),
        (1, 'click'),
        (2, 'click_and_hold'),
        (3, 'context_click'),
        (4, 'double_click'),
        (5, 'release'),
        (6, 'move_by_offset'),
        (7, 'move_to_element'),
        (8, 'move_to_element_with_offset'),
        (9, 'drag_and_drop'),
        (10, 'drag_and_drop_by_offset'),
        (11, 'key_down'),
        (12, 'key_up'),
        (13, 'send_keys'),
        (14, 'send_keys_to_element'),
    )
    ui_special_action = models.IntegerField(choices=ui_special_action_list, default=0)
    ui_alert_handle_list = (
        (0, ''),
        (1, 'accept'),
        (2, 'dismiss'),
        (3, 'ignore'),
    )
    ui_alert_handle = models.IntegerField(choices=ui_alert_handle_list, default=0)
    api_url = models.TextField(blank=True)
    api_headers = models.TextField(blank=True)
    api_body = models.TextField(blank=True)
    api_data = models.TextField(blank=True)
    other_sub_case = models.ForeignKey('main.Case', on_delete=models.DO_NOTHING, blank=True, null=True, related_name='step_sub_case')

    class Meta:
        # db_table = 'test_case_step'
        ordering = ['-pk']
        pass

    def __str__(self):
        return self.name


# 用例和步骤关系表
class CaseVsStep(models.Model):
    case = models.ForeignKey('main.Case', on_delete=models.DO_NOTHING)
    step = models.ForeignKey('main.Step', on_delete=models.DO_NOTHING)
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='case_vs_step_creator',
                                on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='case_vs_step_modifier',
                                 on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        unique_together = ('case', 'step', 'order')
        ordering = ['case', 'order']

    # def case_id(self):
    #     return self.case.id
    #
    # def step_id(self):
    #     return self.step.id

    def __str__(self):
        return '{} [{}]<===>{} [{}]'.format(self.case.id, self.case.name, self.step.id, self.step.name)


# 动作（关键字）表
class Action(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='action_creator', on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='action_modifier', on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    type = models.ForeignKey('main.ActionType', on_delete=models.DO_NOTHING)

    @property
    def full_name(self):
        return '{} - {}'.format(self.type, self.name)

    class Meta:
        unique_together = ('name', 'type')

    def __str__(self):
        return self.full_name

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.full_name


# 步骤类型字典表
class ActionType(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    def __str__(self):
        return self.name


# 配置表
class Config(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='config_creator', on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='config_modifier', on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    ui_selenium_client_list = (
        (0, '不启用'),
        (1, 'Selenium - 本地'),
        (2, 'Selenium - 远程'),
    )
    ui_selenium_client = models.IntegerField(choices=ui_selenium_client_list, default=0)
    ui_remote_ip = models.CharField(max_length=100, blank=True, default='')
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
    ui_driver_ff_profile = models.CharField(max_length=100, blank=True, default='')

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    def __str__(self):
        return self.name


# 变量组表
class VariableGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='variable_group_creator',
                                on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='variable_group_modifier',
                                 on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    def __str__(self):
        return self.name


# 变量表
class Variable(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    value = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    variable_group = models.ForeignKey('main.VariableGroup', on_delete=models.DO_NOTHING)

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'variable_group')


# 测试套件
class Suite(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='suite_creator', on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='suite_modifier', on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    base_timeout = models.FloatField(default=10)
    ui_get_ss = models.BooleanField(default=True)
    log_level_list = (
        (0, 'NOTSET'),
        (10, 'DEBUG'),
        (20, 'INFO'),
        (30, 'WARNING'),
        (40, 'ERROR'),
        (50, 'CRITICAL'),
    )
    log_level = models.IntegerField(choices=log_level_list, default=20)
    console_log_level = models.IntegerField(choices=log_level_list, default=20)
    thread_count = models.IntegerField(default=1)
    config = models.ForeignKey('main.Config', on_delete=models.DO_NOTHING)
    variable_group = models.ForeignKey('main.VariableGroup', on_delete=models.DO_NOTHING, blank=True, null=True)
    case = models.ManyToManyField('Case', through='SuiteVsCase', through_fields=('suite', 'case'))

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    def __str__(self):
        return self.name


# 测试套件和用例的对应关系
class SuiteVsCase(models.Model):
    suite = models.ForeignKey('main.Suite', on_delete=models.DO_NOTHING)
    case = models.ForeignKey('main.Case', on_delete=models.DO_NOTHING)
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='suite_vs_case_creator',
                                on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='suite_vs_case_modifier',
                                 on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        unique_together = ('suite', 'case', 'order')
        ordering = ['suite', 'order']

    def __str__(self):
        return '{} [{}]<===>{} [{}]'.format(self.suite.id, self.suite.name, self.case.id, self.case.name)


# suite测试结果
class SuiteResult(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    is_active = models.BooleanField(default=True)

    base_timeout = models.FloatField(default=10)
    ui_get_ss = models.BooleanField(default=True)
    thread_count = models.IntegerField(default=1)
    config = models.TextField(blank=True, null=True)
    variable_group = models.TextField(blank=True, null=True)

    suite = models.ForeignKey('main.Suite', on_delete=models.DO_NOTHING)
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='suite_result_creator',
                                on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='suite_result_modifier',
                                 on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    execute_count = models.IntegerField(blank=True, null=True)
    pass_count = models.IntegerField(blank=True, null=True)
    fail_count = models.IntegerField(blank=True, null=True)
    error_count = models.IntegerField(blank=True, null=True)

    result_status_list = (
        (1, '成功'),
        (2, '失败'),
        (3, '异常'),
    )
    result_status = models.IntegerField(blank=True, null=True)

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
            from py_test.vic_tools.vic_date_handle import get_timedelta_str
            return get_timedelta_str(self.elapsed_time, 1)


# case测试结果
class CaseResult(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)

    variable_group = models.TextField(blank=True, null=True)

    suite_result = models.ForeignKey('main.SuiteResult', on_delete=models.DO_NOTHING)
    step_result = models.ForeignKey('main.StepResult', on_delete=models.DO_NOTHING, blank=True, null=True)
    parent_case_pk_list = models.TextField(blank=True, null=True)
    case = models.ForeignKey('main.Case', on_delete=models.DO_NOTHING)
    case_order = models.IntegerField(blank=True, null=True)
    creator = models.ForeignKey(User, verbose_name='创建人', on_delete=models.DO_NOTHING)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    execute_count = models.IntegerField(blank=True, null=True)
    pass_count = models.IntegerField(blank=True, null=True)
    fail_count = models.IntegerField(blank=True, null=True)
    error_count = models.IntegerField(blank=True, null=True)

    result_status_list = (
        (1, '成功'),
        (2, '失败'),
        (3, '异常'),
    )
    result_status = models.IntegerField(blank=True, null=True)
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
            from py_test.vic_tools.vic_date_handle import get_timedelta_str
            return get_timedelta_str(self.elapsed_time, 1)


# step测试结果
class StepResult(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    keyword = models.CharField(blank=True, max_length=100)
    action = models.CharField(blank=True, max_length=100)

    case_result = models.ForeignKey('main.CaseResult', on_delete=models.DO_NOTHING)
    step = models.ForeignKey('main.Step', on_delete=models.DO_NOTHING)
    step_order = models.IntegerField(blank=True, null=True)

    creator = models.ForeignKey(User, verbose_name='创建人', on_delete=models.DO_NOTHING)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    result_status_list = (
        (1, '成功'),
        (2, '失败'),
        (3, '异常'),
    )
    result_status = models.IntegerField(blank=True, null=True)
    result_message = models.TextField(blank=True)
    result_error = models.TextField(blank=True)

    step_snapshot = models.TextField(blank=True, null=True)
    has_sub_case = models.BooleanField(default=False)

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
            from py_test.vic_tools.vic_date_handle import get_timedelta_str
            return get_timedelta_str(self.elapsed_time, 1)


class Image(models.Model):
    name = models.CharField(max_length=100)
    img = models.ImageField(upload_to='img')
