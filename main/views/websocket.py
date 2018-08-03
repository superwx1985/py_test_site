import logging
from channels.generic.websocket import WebsocketConsumer
from channels.consumer import SyncConsumer
from channels.exceptions import StopConsumer
import json
import time
from main.models import Suite
from py_test.general.execute_suite import execute_suite
from django.urls import reverse
from django.template.loader import render_to_string
from utils.system import FORCE_STOP


class SuiteConsumer(WebsocketConsumer):
    def connect(self):
        if self.scope['user'].is_authenticated:
            self.accept()
            self.send(text_data=json.dumps({'type': 'ready'}))
        else:
            self.close()

    def sender(self, msg, level):
        try:
            self.send(text_data=json.dumps({'type': 'message', 'message': msg, 'level': level}))
        # 如果websocket客户端被意外关闭
        except KeyError:
            pass

    def receive(self, text_data):
        user = self.scope['user']
        if user.is_authenticated:
            text_data_json = json.loads(text_data)
            command = text_data_json['command']
            execute_uuid = text_data_json['execute_uuid']
            if command == 'start':
                try:
                    suite_pk = self.scope['url_route']['kwargs']['suite_pk']
                except KeyError as e:
                    self.send(text_data=json.dumps({'type': 'error', 'message': e}), close=True)
                else:
                    suite_ = Suite.objects.get(pk=suite_pk, is_active=True)
                    suite_result = execute_suite(suite_, self.scope['user'], execute_uuid, self.sender)
                    sub_objects = suite_result.caseresult_set.filter(step_result=None).order_by('case_order')
                    suite_result_content = render_to_string('main/include/suite_result_content.html', locals())
                    data_dict = dict()
                    data_dict['suite_result_content'] = suite_result_content
                    data_dict['suite_result_url'] = reverse('result', args=[suite_result.pk])
                    self.send(text_data=json.dumps({'type': 'end', 'data': data_dict}), close=True)
            elif command == 'stop':
                FORCE_STOP[execute_uuid] = user.pk
                self.send(text_data=json.dumps({'type': 'message', 'message': '正在强制停止...'}), close=True)


class ChatConsumer(SyncConsumer):
    def websocket_connect(self, message):
        if self.scope['user'].is_authenticated:
            self.send({
                "type": "websocket.accept"
            })

            text_json = json.dumps({'message': '{}'.format('init')})
            self.send(
                {
                    "type": "websocket.send",
                    "text": text_json
                },
            )
        else:
            raise StopConsumer

    def websocket_receive(self, message):
        text_data = message.get('text', {})

        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')

        text_json = json.dumps({'message': '{} - {}'.format(0, message)})

        self.send(
            {
                "type": "websocket.send",
                "text": text_json
            },
        )

        for i in range(1, 4):
            time.sleep(1)
            text_json = json.dumps({'message': '{} - {}'.format(i, message)})
            self.send(
                {
                    "type": "websocket.send",
                    "text": text_json
                },
            )

        self.send({"type": "websocket.close"})

    def websocket_disconnect(self, message):
        raise StopConsumer
