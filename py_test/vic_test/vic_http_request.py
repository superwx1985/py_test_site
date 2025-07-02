import requests
import uuid
import json
from loguru import logger


def get_cookies_str(_cookies):
    cookies_str = ""
    for _ in _cookies:
        cookies_str = f"{cookies_str}\n_" if cookies_str else _
    return cookies_str


def print_request_info(prepared_request, logger):
    msg = f"""
====================
Request ID: {prepared_request.id}
Request URL: {prepared_request.url}
Request Method: {prepared_request.method}
Request Headers:\n{prepared_request.headers}
Request Body:\n{prepared_request.body}
===================="""
    logger.info(msg)


def print_response_info(response, logger, highlight_error=False):
    msg = f"""
====================
Request ID: {response.id}
Response Code: {response.status_code}
Response Headers:\n{response.headers}
Response Message:\n{response.text}
===================="""
    if highlight_error and response.status_code >= 400:
        logger.error(msg)
    else:
        logger.info(msg)


def vic_requests(
        method, url, headers=None, files=None, data=None, params=None, auth=None, cookies=None, hooks=None,
        json=None, _logger=None, highlight_error=False, timeout=(10, 60),
        session=None, allow_redirects=True, max_redirects=30):
    if session is None:
        session = requests.Session()
    if allow_redirects is None:
        allow_redirects = True
    if max_redirects is None:
        max_redirects = 30
    session.max_redirects = max_redirects
    _id = str(uuid.uuid4())
    req = requests.Request(method, url, headers, files, data, params, auth, cookies, hooks, json)
    prepared_request = session.prepare_request(req)
    prepared_request.id = _id
    if _logger is not None:
        print_request_info(prepared_request, _logger)
    rep = session.send(prepared_request, timeout=timeout, allow_redirects=allow_redirects)
    rep.id = _id
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

    response = vic_requests(method, url, headers, files, data, params, auth, cookies, hooks, json, _logger=logger, highlight_error=True)
