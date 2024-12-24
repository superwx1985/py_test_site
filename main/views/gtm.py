import requests
import json
from django.http import HttpResponseRedirect, JsonResponse, Http404, HttpResponseForbidden
import py_test_site.settings as settings


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
        r = requests.request("POST", url=url, headers=headers, data=body)

        tc_data = json.loads(r.text)[0]
        tc_id = tc_data['tcId']
        project_id = tc_data['projectId']
        iterations_dict = tc_data.pop("iterations")
        test_data = {"data": [], "tcNumber": tc_number, "version": version, "tcId": tc_id, "projectId": project_id}
        for key, value in iterations_dict.items():
            test_data["data"].append(value)

        return JsonResponse(test_data)
    else:
        return HttpResponseForbidden
