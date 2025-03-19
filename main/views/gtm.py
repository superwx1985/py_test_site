import json
import logging
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.conf import settings
from py_test.vic_test.vic_http_request import request

logger = logging.getLogger('django.request')


@login_required
def get_gtm_data(request):
    if request.method == 'POST':
        condition = request.POST.get('condition', '{}')
        try:
            condition = json.loads(condition)
        except json.decoder.JSONDecodeError:
            condition = dict()
        test_data = get_gtm_data_(condition.get('tcNumber'), condition.get('version'))
        return JsonResponse(test_data)
    else:
        return HttpResponseForbidden


def get_gtm_data_(tc_number, version):
    url = f"{settings.GLB.get("GTM_BASE_URL")}/api/getTestData"
    headers = {
        'Content-Type': 'application/json',
    }
    body = json.dumps([{
        "tcNumber": tc_number,
        "version": version
    }])
    test_data = {"data": [], "tcNumber": tc_number, "version": version, "tcId": None, "projectId": None}
    try:
        r = request("POST", url=url, headers=headers, data=body, _logger=logger)
        tc_data = json.loads(r.text)[0]
        tc_id = tc_data['tcId']
        project_id = tc_data['projectId']
        iterations_dict = tc_data.pop("iterations")
        test_data["tcId"] = tc_id
        test_data["projectId"] = project_id
        if iterations_dict:
            for key, value in iterations_dict.items():
                test_data["data"].append(value)
    except Exception as e:
        logger.warning('未能获取gtm数据', exc_info=True)
    return test_data
