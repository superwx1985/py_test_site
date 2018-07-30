import logging
from channels.generic.websocket import WebsocketConsumer
from channels.consumer import SyncConsumer
from channels.exceptions import StopConsumer
import json
import time
from main.models import Suite
from py_test.general.execute_suite import execute_suite


class SuiteConsumer(WebsocketConsumer):
    def connect(self):
        if self.scope['user'].is_authenticated:
            self.accept()
            self.send(text_data=json.dumps({'message': 'start'}))
            try:
                suite_pk = self.scope['url_route']['kwargs']['suite_pk']
            except KeyError as e:
                self.send(text_data=json.dumps({'message': e}), close=True)
            else:
                suite_ = Suite.objects.get(pk=suite_pk, is_active=True)
                suite_result = execute_suite(suite_, self.scope['user'], self.sender)
                print(suite_result)
                self.close()
        else:
            self.close()

    def sender(self, msg):
        self.send(text_data=json.dumps({'message': msg}))


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
