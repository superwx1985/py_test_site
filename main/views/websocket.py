from channels.generic.websocket import WebsocketConsumer
import json
from urllib.parse import parse_qs
from main.models import Suite, Token
from py_test.general.execute_suite import execute_suite
from django.urls import reverse
from django.template.loader import render_to_string
from utils.system import FORCE_STOP


class SuiteConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        if self.get_user():
            self.send(text_data=json.dumps({'type': 'ready'}))
        else:
            self.send(text_data=json.dumps({'type': 'error', 'data': '无效用户'}), close=True)

    def sender(self, msg, level):
        try:
            self.send(text_data=json.dumps({'type': 'message', 'message': msg, 'level': level}))
        # 如果websocket客户端被意外关闭
        except KeyError:
            pass

    def receive(self, text_data=None, bytes_data=None):
        user = self.get_user()
        if user:
            text_data_json = json.loads(text_data)
            command = text_data_json['command']
            execute_uuid = text_data_json['execute_uuid']
            if command == 'start':
                try:
                    pk = int(self.get_pk())
                except KeyError as e:
                    self.send(text_data=json.dumps({'type': 'error', 'message': e}), close=True)
                except ValueError as e:
                    self.send(text_data=json.dumps({'type': 'error', 'message': e}), close=True)
                else:
                    suite_ = Suite.objects.get(pk=pk, is_active=True)
                    suite_result = execute_suite(suite_, user, execute_uuid, self.sender)
                    data_dict = self.get_result_data(suite_result)
                    self.send(text_data=json.dumps({'type': 'end', 'data': data_dict}), close=True)
            elif command == 'stop':
                FORCE_STOP[execute_uuid] = user.pk
                self.send(text_data=json.dumps({'type': 'message', 'message': '已接收到强制停止指令，将在本步骤完成后停止执行。'}), close=True)
        else:
            self.send(text_data=json.dumps({'type': 'error', 'data': 'token无效'}), close=True)

    def get_user(self):
        user = self.scope['user']
        if user.is_authenticated:
            return user
        else:
            return None

    def get_pk(self):
        return self.scope['url_route']['kwargs']['suite_pk']

    @staticmethod
    def get_result_data(suite_result):
        sub_objects = suite_result.caseresult_set.filter(step_result=None).order_by('case_order')
        suite_result_content = render_to_string('main/include/suite_result_content.html', locals())
        data_dict = dict()
        data_dict['suite_result_content'] = suite_result_content
        data_dict['suite_result_status'] = suite_result.result_status
        data_dict['suite_result_url'] = reverse('result', args=[suite_result.pk])
        return data_dict


class SuiteRemoteConsumer(SuiteConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = str(self.scope['query_string'], encoding='utf-8')
        self.qs_dict = parse_qs(qs)

    def get_user(self):
        token = self.qs_dict.get('token')[0]
        try:
            user = Token.objects.get(value=token).user
        except Token.DoesNotExist:
            return None
        if user.is_authenticated:
            return user
        else:
            return None

    def get_pk(self):
        return self.qs_dict.get('pk')[0]

    @staticmethod
    def get_result_data(result):
        data_dict = dict()
        data_dict['suite_result_status'] = result.result_status
        data_dict['suite_result_url'] = reverse('result', args=[result.pk])
        return data_dict

