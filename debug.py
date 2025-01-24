import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "py_test_site.settings")
django.setup()
from main.models import *


def combine_json_fields():
    from django.forms.models import model_to_dict
    # 获取模型
    # MyModel = apps.get_model('main', 'suiteresult')
    MyModel = SuiteResult
    for obj in MyModel.objects.all():
        if not obj.snapshot:
            suite = obj.suite
            _snapshot = model_to_dict(suite) if suite else None
            _snapshot['case'] = [x.pk for x in _snapshot['case']]

            _snapshot["timeout"] = obj.timeout
            _snapshot["ui_step_interval"] = obj.ui_step_interval
            _snapshot["ui_get_ss"] = obj.ui_get_ss
            _snapshot["thread_count"] = obj.thread_count

            obj.snapshot = _snapshot
        obj.save()


if __name__ == '__main__':
    combine_json_fields()
