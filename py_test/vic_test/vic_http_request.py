import requests
import uuid
import json
from loguru import logger


def print_request_info(prepared_request, logger):
    msg = f"""
====================
Request ID: {prepared_request._id}
Request URL: {prepared_request.url}
Request Method: {prepared_request.method}
Request Headers: {prepared_request.headers}
Request Body: {prepared_request.body}
===================="""
    logger.info(msg)


def print_response_info(response, logger, highlight_error=False):
    msg = f"""
====================
Request ID: {response._id}
Response Code: {response.status_code}
Response Message: {response.text}
===================="""
    if highlight_error and response.status_code >= 400:
        logger.error(msg)
    else:
        logger.info(msg)


def request(method, url, headers=None, files=None, data=None, params=None, auth=None, cookies=None, hooks=None,
            json=None, _logger=None, highlight_error=False, timeout=(10, 60)):
    session = requests.Session()
    _id = str(uuid.uuid4())
    req = requests.Request(method, url, headers, files, data, params, auth, cookies, hooks, json)
    prepared_request = session.prepare_request(req)
    prepared_request._id = _id
    if _logger is not None:
        print_request_info(prepared_request, _logger)
    rep = session.send(prepared_request, timeout=timeout)
    rep._id = _id
    if _logger is not None:
        print_response_info(rep, _logger, highlight_error)
    return rep


if __name__ == '__main__':
    method = "POST"
    url = "https://api.globe-groups.com/globe/world/country/getRegion"
    headers = {"Content-Type": "application/json"}
    files = None
    data = json.dumps({
        "merchantId": "100000000000000000",
        "type": "1",
        "regionIso3": "SWE"
    })
    params = None
    auth = None
    cookies = None
    hooks = None

    response = request(method, url, headers, files, data, params, auth, cookies, hooks, json, _logger=logger, highlight_error=True)
