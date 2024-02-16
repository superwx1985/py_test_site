import json
from channels.generic.websocket import WebsocketConsumer
from urllib.parse import parse_qs
from main.models import Suite, Token
from py_test.general.vic_suite import VicSuite
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils import timezone
from utils.system import RUNNING_SUITES
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User


class SuiteConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        if self.get_user():
            self.send(text_data=json.dumps({'type': 'ready'}))
        else:
            self.send(text_data=json.dumps({'type': 'error', 'data': '用户鉴权失败'}), close=True)

    def sender(self, msg, level, _type='message'):
        try:
            self.send(text_data=json.dumps({'type': _type, 'message': msg, 'level': level}))
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
                    self.send(text_data=json.dumps({'type': 'error', 'data': e}), close=True)
                except ValueError as e:
                    self.send(text_data=json.dumps({'type': 'error', 'data': e}), close=True)
                else:
                    try:
                        suite_ = Suite.objects.get(pk=pk, is_active=True)
                    except Suite.DoesNotExist:
                        self.send(text_data=json.dumps({'type': 'error', 'data': '找不到对应的测试套件'}), close=True)
                    else:
                        print("=========================")
                        print(suite_, type(suite_))
                        vic_suite = VicSuite(suite_, user, execute_uuid, self.sender)
                        vic_suite.execute()
                        data_dict = self.get_result_data(vic_suite.suite_result)
                        self.send(text_data=json.dumps({'type': 'end', 'data': data_dict}), close=True)
            elif command == 'stop':
                self.send(text_data=json.dumps({'type': 'message', 'message': '中止...'}))
                _, msg = RUNNING_SUITES.stop_suite(execute_uuid)
                self.send(text_data=json.dumps({'type': 'message', 'message': msg}), close=True)
            elif command == 'pause':
                self.send(text_data=json.dumps({'type': 'message', 'message': '暂停...'}))
                success, msg = RUNNING_SUITES.pause_suite(execute_uuid)
                if success:
                    self.send(text_data=json.dumps({'type': 'pause'}))
                self.send(text_data=json.dumps({'type': 'message', 'message': msg}), close=True)
            elif command == 'continue':
                self.send(text_data=json.dumps({'type': 'message', 'message': '继续...'}))
                success, msg = RUNNING_SUITES.continue_suite(execute_uuid)
                if success:
                    self.send(text_data=json.dumps({'type': 'continue'}))
                self.send(text_data=json.dumps({'type': 'message', 'message': msg}), close=True)
        else:
            self.send(text_data=json.dumps({'type': 'error', 'data': 'token无效'}), close=True)

    def get_user(self):
        user = self.scope.get('user', None)
        # debug模式scope没有user信息，只能通过session查找user
        if user and user.is_authenticated:
            return user
        else:
            try:
                headers = self.scope["headers"]
                session_id = None
                for _ in headers:
                    if b"cookie" == _[0]:
                        cookie_string = _[1].decode('utf-8')
                        start_index = cookie_string.find("sessionid=")
                        if start_index != -1:
                            # sessionid 子字符串的起始位置是等号的后一个位置
                            start_index += len("sessionid=")
                            # 找到 sessionid 子字符串的结束位置（分号的位置）
                            end_index = cookie_string.find(";", start_index)
                            # 如果没有找到分号，说明 sessionid 是字符串的最后一个部分
                            if end_index == -1:
                                session_id = cookie_string[start_index:]
                            else:
                                session_id = cookie_string[start_index:end_index]
                            break
                session = Session.objects.get(session_key=session_id)
                # 获取会话数据中存储的用户ID
                user_id = session.get_decoded().get('_auth_user_id')
                # 根据用户ID获取用户对象
                user = User.objects.get(pk=user_id)
                return user
            except Session.DoesNotExist:
                return None
            except User.DoesNotExist:
                return None
            except:
                raise

    def get_pk(self):
        return self.scope['url_route']['kwargs']['suite_pk']

    @staticmethod
    def get_result_data(suite_result):
        sub_objects = suite_result.caseresult_set.filter(step_result=None)
        suite_result_content = render_to_string('main/include/suite_result_content.html', locals())
        data_dict = dict()
        data_dict['suite_result_content'] = suite_result_content
        data_dict['suite_result_state'] = suite_result.result_state
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
            user = Token.objects.get(value=token, expire_date__gt=timezone.now()).user
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
        data_dict['suite_result_state'] = result.result_state
        data_dict['suite_result_url'] = reverse('result', args=[result.pk])
        return data_dict

