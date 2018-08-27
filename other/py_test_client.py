import websocket
import json
import uuid
import logging.handlers
import sys
import urllib.parse


class NonWarningFilter(logging.Filter):
    def filter(self, record):
        if record.levelno >= 30:
            return False
        return True


def get_log_level_name(levelno):
    if levelno <= 0:
        level_name = 'notset'
    elif levelno <= 10:
        level_name = 'debug'
    elif levelno <= 20:
        level_name = 'info'
    elif levelno <= 30:
        level_name = 'warning'
    elif levelno <= 40:
        level_name = 'error'
    else:
        level_name = 'critical'
    return level_name


run_result = None
logger = logging.getLogger('py_test_client')

format_ = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')

info_handler = logging.StreamHandler(stream=sys.stdout)
info_handler.setLevel(logging.DEBUG)
info_handler.setFormatter(format_)
info_handler.addFilter(NonWarningFilter())

error_handler = logging.StreamHandler(stream=sys.stderr)
error_handler.setLevel(logging.WARNING)
error_handler.setFormatter(format_)

logger.addHandler(info_handler)
logger.addHandler(error_handler)
logger.setLevel(logging.INFO)


def on_message(ws, message):

    try:
        msg_obj = json.loads(message)
    except json.decoder.JSONDecodeError:
        logger.warning('接收到的消息不是有效的json格式')
    else:
        if msg_obj['type'] == 'ready':
            ws.send(json.dumps({'command': 'start', 'execute_uuid': str(uuid.uuid1())}))
        elif msg_obj['type'] == 'message':
            msg_level = msg_obj.get('level', logging.INFO)
            msg_level_name = get_log_level_name(msg_level)
            try:
                logger_level = getattr(logger, msg_level_name)
            except AttributeError:
                logger_level = logger.info
            logger_level(msg_obj['message'])
        elif msg_obj['type'] == 'error':
            logger.error(msg_obj['data'])
        elif msg_obj['type'] == 'end':
            global run_result
            run_result = msg_obj['data']


def on_error(ws, error):
    logger.error(error)


def on_close(ws):
    logger.debug("### websocket closed ###")


def on_open(ws):
    logger.debug("### websocket open ###")


if __name__ == "__main__":
    from sys import argv

    # 需要N个参数
    n = 5
    msg = '''只接收到[{}]个参数。请提供[{}]个参数，依次是：
1. 测试服务器地址
2. 套件ID
3. token
4. websocket超时设置（秒）
5. 日志级别（10/20/30/40/50）'''

    if len(argv) < n + 1:
        raise ValueError(msg.format(len(argv) - 1, n))
    test_server = str(argv[1])
    pk = str(argv[2])
    token = str(argv[3])
    timeout = int(argv[4])
    level = int(argv[5])

    # websocket.enableTrace(True)  # 打印连接信息

    logger.setLevel(level)
    pk = urllib.parse.quote(pk, encoding='utf-8')
    token = urllib.parse.quote(token, encoding='utf-8')
    ws_url = 'ws://{}/ws/suite_execute_remote/?pk={}&token={}'.format(test_server, pk, token)
    logger.debug('尝试建立websocket连接：{}'.format(ws_url))
    ws = websocket.WebSocketApp(
        url=ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.on_open = on_open
    ws.run_forever(ping_timeout=timeout)
    if run_result:
        suite_result_status = run_result.get('suite_result_status')
        suite_result_url = run_result.get('suite_result_url')
        if suite_result_url:
            logger.info('测试结果页面：http://{}{}'.format(test_server, suite_result_url))
        else:
            logger.warning('找不到测试结果页')
        assert suite_result_status, '测试意外终止或结果入库失败'
        assert run_result['suite_result_status'] == 1, '本次测试未通过'
    else:
        raise ConnectionError('服务器未能返回测试结果')
