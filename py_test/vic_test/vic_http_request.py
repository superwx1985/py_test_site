import httplib2, json
from urllib.parse import quote   #用于转换url编码

def http_request(url,url_params=None,method=None,headers=None,body=None,print_=False):
    full_url = url
    method = method.upper()
    if url_params:
        full_url=full_url+'?'
        for key, value in url_params.items():
            full_url = full_url+key+'='+quote(value)+'&'    #字典内的文本转换成URL编码，然后拼接成URL
        full_url=full_url.rstrip('&')
    if body:
        if isinstance(body, dict):
            body = json.dumps(body,indent=4)    #把字典转换为格式化的文本
        else:
            body = body
            print(body)
        #body = str(data).replace('\'', '\"')
    if print_:
        print('[url]\n%s\n\n[method]\n%s\n\n[headers]\n%s\n\n[body]\n%s\n\n' %(full_url,method,headers,body))
    h = httplib2.Http()
    response, content = h.request(uri=full_url, method=method, headers=headers, body=body)
    try:
        str_content = content.decode('utf-8')   #处理中文乱码
    except UnicodeDecodeError:
        try:
            str_content = content.decode('GBK') #处理中文乱码
        except:
            str_content = str(content)
    return response, str_content


if __name__ == '__main__':
    url = 'http://retailerapi-qa-1048811846.us-east-1.elb.amazonaws.com/retailer/v1/registry'
    url_params = {'apikey':'ca7f6e91ee8134de9717707d86b29100'}
    method = 'post'
    headers = {'access-key':'839d35cd515746b5167d494f856e4ef0','Content-Type':'application/json; charset=utf-8'}
    body1 = {
"RetailerRegistryCode": "AUTOMATIONTEST20150607",
"RegistrantFirstName": "AUTOMATIONTEST20150607",
"RegistrantLastName": "TEST-R",  
"RegistrantEmail": "AUTOMATIONTEST20150607@gmail.com",
"CoRegistrantFirstName": "AUTOMATIONTEST20150607",
"CoRegistrantLastName": "TEST-C",
"CoRegistrantEmail": "AUTOMATIONTEST20150607@gmail.com",
"City": "OMAHA",
"State": "NE",
"Zip": "68154",
"EventTypeId": 1,
"EventDate": "2016-01-28",
"EventDescription": "",
"ReferralStatusCode": "",
"RegistryClickId": "",
"AltRetailerRegistryCode": "",
"ModifiedDate": "2015-12-04"
}
    body2='''
{
    "RegistryClickId": "",
    "EventDate": "2016-01-28",
    "RetailerRegistryCode": "AUTOMATIONTEST20150607",
    "CoRegistrantFirstName": "AUTOMATIONTEST20150607",
    "RegistrantEmail": "AUTOMATIONTEST20150607@gmail.com",
    "ModifiedDate": "2015-12-04",
    "EventTypeId": 1,
    "City": "OMAHA",
    "CoRegistrantEmail": "AUTOMATIONTEST20150607@gmail.com",
    "AltRetailerRegistryCode": "",
    "RegistrantLastName": "TEST-R",
    "Zip": "68154",
    "EventDescription": "",
    "State": "NE",
    "ReferralStatusCode": "",
    "RegistrantFirstName": "AUTOMATIONTEST20150607",
    "CoRegistrantLastName": "TEST-C"
}
'''
    response, content = http_request(url=url,url_params=url_params,method=method,headers=headers,body=body2,print_=True)
    print('[response]\n%s\n\n[content]\n%s' %(response,content))