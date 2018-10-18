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


def get_logger_with_level(levelno, _logger):
    if levelno <= 0:
        level_logger = _logger.notset
    elif levelno <= 10:
        level_logger = _logger.debug
    elif levelno <= 20:
        level_logger = _logger.info
    elif levelno <= 30:
        level_logger = _logger.warning
    elif levelno <= 40:
        level_logger = _logger.error
    else:
        level_logger = _logger.critical
    return level_logger


run_result = None
logger = logging.getLogger('py_test_client')
test_logger = logging.getLogger('test_logger')

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

test_logger.addHandler(info_handler)
test_logger.addHandler(error_handler)
test_logger.setLevel(logging.DEBUG)


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
            level_logger = get_logger_with_level(msg_level, test_logger)
            level_logger(msg_obj['message'])
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
    import argparse

    parser = argparse.ArgumentParser(description='py_test命令行客户端')
    parser.add_argument(
        "-s",
        "--server",
        help="测试服务器地址",
        required=True,
    )
    parser.add_argument(
        "-i",
        "--id",
        dest="suite_id",
        help="测试套件ID",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--token",
        help="授权token",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--timeout",
        type=int,
        help="客户端超时设置（秒）",
        default=300,
    )
    parser.add_argument(
        "-l",
        "--log_level",
        type=int,
        help="客户端日志级别（1=DEBUG，2=INFO，3=WARNING，4=ERROR，5=CRITICAL）",
        choices=[1, 2, 3, 4, 5],
        default=2,
    )

    args = parser.parse_args(argv[1:])

    test_server = args.server
    pk = args.suite_id
    token = args.token
    timeout = args.timeout
    log_level = args.log_level*10

    if log_level <= logging.DEBUG:
        websocket.enableTrace(True)  # 打印连接信息

    logger.setLevel(log_level)
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
