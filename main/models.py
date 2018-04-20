from django.db import models
from django.contrib.auth.models import User


class Case(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    keyword = models.CharField(max_length=256, blank=True, default='')
    # creator = models.CharField('创建人', max_length=256, editable=False, default='')
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='case_creator', on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    # modifier = models.CharField('修改人', max_length=256, editable=False, default='')
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='case_modifier', on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_valid = models.BooleanField(default=True)
    config = models.ForeignKey('main.Config', on_delete=models.DO_NOTHING)
    step = models.ManyToManyField('Step', through='CaseVsStep', through_fields=('case', 'step'))

    # tcg = models.ForeignKey(TcGroup, related_name='tcg')
    # type = models.ForeignKey(Type)

    class Meta:
        pass
        # db_table = 'test_case_step'
        ordering = ['name']  # 这个字段是告诉Django模型对象返回的记录结果集是按照哪个字段排序的,-xxx表示降序，?xxx表示随机

    def __str__(self):
        return self.name


class Step(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    keyword = models.CharField(max_length=256, blank=True, default='')
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='step_creator', on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='step_modifier', on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_valid = models.BooleanField(default=True)
    action = models.ForeignKey('main.Action')
    timeout = models.FloatField(blank=True, null=True)
    save_as = models.CharField(blank=True, max_length=256)
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
    ui_ui_alert_handle_list = (
        (0, ''),
        (1, 'accept'),
        (2, 'dismiss'),
        (3, 'ignore'),
    )
    ui_alert_handle = models.IntegerField(choices=ui_ui_alert_handle_list, default=0)
    api_url = models.TextField(blank=True)
    api_headers = models.TextField(blank=True)
    api_body = models.TextField(blank=True)
    api_data = models.TextField(blank=True)

    class Meta:
        # db_table = 'test_case_step'
        ordering = ['name']
        pass

    def __str__(self):
        return self.name


class CaseVsStep(models.Model):
    case = models.ForeignKey('main.Case')
    step = models.ForeignKey('main.Step')
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='case_vs_step_creator',
                                on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='case_vs_step_modifier',
                                 on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_valid = models.BooleanField(default=True)
    order = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('case', 'step')
        ordering = ['case', 'order']

    def case_id(self):
        return '{}'.format(self.case.id)

    def step_id(self):
        return '{}'.format(self.step.id)

    def __str__(self):
        return '{} [{}]<===>{} [{}]'.format(self.case.id, self.case.name, self.step.id, self.step.name)


class Action(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    keyword = models.CharField(max_length=256, blank=True, default='')
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='action_creator', on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='action_modifier', on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_valid = models.BooleanField(default=True)
    type = models.ForeignKey('main.ActionType')

    class Meta:
        unique_together = ('name', 'type')

    def __str__(self):
        return '{} - {}'.format(self.type, self.name)


class ActionType(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    keyword = models.CharField(max_length=256, blank=True, default='')
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='action_type_creator',
                                on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='action_type_modifier',
                                 on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_valid = models.BooleanField(default=True)

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    def __str__(self):
        return self.name


class Config(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    keyword = models.CharField(max_length=256, blank=True, default='')
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='config_creator', on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='config_modifier', on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_valid = models.BooleanField(default=True)

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    def __str__(self):
        return self.name


class Group(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    keyword = models.CharField(max_length=256, blank=True, default='')
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='group_creator', on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    modifier = models.ForeignKey(User, verbose_name='修改人', related_name='group_modifier', on_delete=models.DO_NOTHING)
    modified_date = models.DateTimeField('修改时间', auto_now=True, null=True)
    is_valid = models.BooleanField(default=True)

    def natural_key(self):  # 序列化时，可以用此值代替外键ID
        return self.name

    def __str__(self):
        return self.name
