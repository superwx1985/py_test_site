import requests
import json
import logging
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponseForbidden
import py_test_site.settings as settings

logger = logging.getLogger('django.request')

def get_gtm_data(request):
    if request.method == 'POST':
        condition = request.POST.get('condition', '{}')
        try:
            condition = json.loads(condition)
        except json.decoder.JSONDecodeError:
            condition = dict()

        tc_number = condition.get('tcNumber')
        version = condition.get('version')

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
            r = requests.request("POST", url=url, headers=headers, data=body)
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
        return JsonResponse(test_data)
    else:
        return HttpResponseForbidden
