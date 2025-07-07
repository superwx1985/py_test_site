from lxml import etree


def parse_xml(xml_string, encoding='utf-8'):
    try:
        parser = etree.XMLParser(encoding=encoding, remove_blank_text=True)
        root = etree.fromstring(xml_string, parser)
    except etree.XMLSyntaxError as e:
        # 回退到 recover 模式
        parser = etree.XMLParser(recover=True, encoding=encoding)
        root = etree.fromstring(xml_string, parser)
    return root


def collect_namespaces(root):
    def _collect_namespaces(element):
        # 收集当前元素的命名空间声明
        for prefix, uri in element.nsmap.items():
            if prefix not in all_ns:
                all_ns[prefix] = uri
        # 递归处理子元素
        for child in element:
            _collect_namespaces(child)

    all_ns = {}
    _collect_namespaces(root)

    # 处理默认命名空间
    if None in all_ns:
        all_ns['_default'] = all_ns.pop(None)
    return all_ns


def find_elements(root, path, namespaces=None):
    namespaces = {} if namespaces is None else namespaces
    return root.xpath(path, namespaces=namespaces)


def vic_find_xml(xml_str, path):
    root = parse_xml(xml_str)
    ns = collect_namespaces(root)
    result = find_elements(root, path, ns)
    str_result = []
    if result:
        for _ in result:
            if isinstance(_, etree._Element):
                str_result.append(etree.tostring(_, encoding='unicode', pretty_print=True, with_tail=True))
            else:
                str_result.append(str(_))

    return str_result


if __name__ == '__main__':
    import pprint
    xml_str = '''
<root>
    <lib:book xmlns:lib="http://example.com/library">
        <lib:row>row lib</lib:row>
        <lib:a class="1">a lib</lib:a>
    </lib:book>
    
    <doc:book xmlns:doc="http://example.com/document">
        <doc:title class="c3">title doc</doc:title>
        <a class="2">a doc</a>
    </doc:book>
    
    <book xmlns="http://example.com/no-key">
        <title class="c3">title no key</title>
        <a class="3">a no key</a>
    </book>
    
    <book><title         class="c3">title no ns1</title>         <a class="4-1">a no ns1</a></book>
    <book><title         class="c3">title no ns2</title>         <a class="4-2">a no ns2</a></book>
</root>
'''
    html_str = '''
<!DOCTYPE html>
<html lang="en">
<!--[if IE 9 ]><html class="ie9"><![endif]-->
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Log in</title>

    <!-- Vendor CSS -->
    <link href="/vendors/bower_components/animate.css/animate.min.css" rel="stylesheet">
    <link href="/vendors/bower_components/material-design-iconic-font/dist/css/material-design-iconic-font.min.css" rel="stylesheet">

    <!-- CSS -->
    <link href="/css/app.min.1.css" rel="stylesheet">
    <link href="/css/app.min.2.css" rel="stylesheet">
    <link href="/css/custom-css.css" rel="stylesheet">
</head>

<body class="login-content">

    <!-- Login -->
    <div class="lc-block toggled" id="l-login">
        <form method="post" action="/Account/Login?Tenant=GLB">
            <input type="hidden" name="returnUrl" value="/connect/authorize/callback?response_type=token&amp;client_id=gConnectWeb&amp;scope=gConnectIotDevice.GUCApi.Write%20gConnectIotDevice.GUCApi.Read%20gConnectIotDevice.offlineMessage.Write%20gConnectIotDevice.testModel.Write%20gConnectIotDevice.testModel.Read%20gConnectIotDevice.Device.Write%20gConnectIotDevice.Device.Read%20gConnectIotDevice.DeviceExtension.Write%20gConnectIotDevice.DeviceExtension.Read%20gConnectIotDevice.RLM.Write%20gConnectIotDevice.RLM.Read%20gConnectIotDevice.UserExtension.Write%20gConnectIotDevice.UserExtension.Read%20user.basic&amp;redirect_uri=https%3A%2F%2Fiot.eu.globetech-groups.com%2Fglb%2Frouter.html" />
            <h3>User Login</h3>
            <div class="text-danger text-left validation-summary-valid" data-valmsg-summary="true"><ul><li style="display:none"></li>
</ul></div>

            <div class="input-group m-b-20">
                <span class="input-group-addon"><i class="zmdi zmdi-account"></i></span>
                <div class="fg-line">
                    <input type="text" class="form-control" placeholder="Email" data-val="true" data-val-required="The Email field is required." id="Email" name="Email" value="">
                </div>
            </div>

            <div class="input-group m-b-20">
                <span class="input-group-addon"><i class="zmdi zmdi-lock"></i></span>
                <div class="fg-line">
                    <input type="password" class="form-control" placeholder="Password" data-val="true" data-val-required="The Password field is required." id="Password" name="Password">
                </div>
            </div>
            <div>
                <a href="/Account/ForgotPassword?returnUrl=%2fconnect%2fauthorize%2fcallback%3fresponse_type%3dtoken%26client_id%3dgConnectWeb%26scope%3dgConnectIotDevice.GUCApi.Write%2520gConnectIotDevice.GUCApi.Read%2520gConnectIotDevice.offlineMessage.Write%2520gConnectIotDevice.testModel.Write%2520gConnectIotDevice.testModel.Read%2520gConnectIotDevice.Device.Write%2520gConnectIotDevice.Device.Read%2520gConnectIotDevice.DeviceExtension.Write%2520gConnectIotDevice.DeviceExtension.Read%2520gConnectIotDevice.RLM.Write%2520gConnectIotDevice.RLM.Read%2520gConnectIotDevice.UserExtension.Write%2520gConnectIotDevice.UserExtension.Read%2520user.basic%26redirect_uri%3dhttps%253A%252F%252Fiot.eu.globetech-groups.com%252Fglb%252Frouter.html">Forgot your password?</a>
                <br />
            </div>
            <div class="clearfix"></div>


            <button class="btn btn-login btn-danger btn-float" type="submit"><i class="zmdi zmdi-arrow-forward"></i></button>

        <input name="__RequestVerificationToken" type="hidden" value="CfDJ8ApRf9-jr0VLla_LOI1b6xduN18CtQC7-9-QOoCnnk3JDr5VP7Vne1jLYGQ-Fq9kp0hVU09DbmTsZifoECycCMss1HacNBeB6COdQym4W3aBwvq_-lKuxs1G5Vax7QxbHXKgksETUJeNgxFf5LTuw7s" /></form>
    </div>


    <!-- Older IE warning message -->
    <!--[if lt IE 9]>
        <div class="ie-warning">
            <h1 class="c-white">Warning!!</h1>
            <p>You are using an outdated version of Internet Explorer, please upgrade <br/>to any of the following web browsers to access this website.</p>
            <div class="iew-container">
                <ul class="iew-download">
                    <li>
                        <a href="http://www.google.com/chrome/">
                            <img src="img/browsers/chrome.png" alt="">
                            <div>Chrome</div>
                        </a>
                    </li>
                    <li>
                        <a href="https://www.mozilla.org/en-US/firefox/new/">
                            <img src="img/browsers/firefox.png" alt="">
                            <div>Firefox</div>
                        </a>
                    </li>
                    <li>
                        <a href="http://www.opera.com">
                            <img src="img/browsers/opera.png" alt="">
                            <div>Opera</div>
                        </a>
                    </li>
                    <li>
                        <a href="https://www.apple.com/safari/">
                            <img src="img/browsers/safari.png" alt="">
                            <div>Safari</div>
                        </a>
                    </li>
                    <li>
                        <a href="http://windows.microsoft.com/en-us/internet-explorer/download-ie">
                            <img src="img/browsers/ie.png" alt="">
                            <div>IE (New)</div>
                        </a>
                    </li>
                </ul>
            </div>
            <p>Sorry for the inconvenience!</p>
        </div>
    <![endif]-->
    <!-- Javascript Libraries -->
    <script src="/vendors/bower_components/jquery/dist/jquery.min.js"></script>
    <script src="/vendors/bower_components/bootstrap/dist/js/bootstrap.min.js"></script>

    <script src="/vendors/bower_components/Waves/dist/waves.min.js"></script>

    <!-- Placeholder for IE9 -->
    <!--[if IE 9 ]>
        <script src="vendors/bower_components/jquery-placeholder/jquery.placeholder.min.js"></script>
    <![endif]-->

    <script src="/js/functions.js"></script>

</body>
</html>
    '''

    # r = vic_find_xml(xml_str, '''//doc:book/a/@class''')

    r = vic_find_xml(html_str, '''//body//input/@value''')
    pprint.pprint(r)
