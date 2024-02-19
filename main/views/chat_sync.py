import time

from django.shortcuts import render
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .websocket import SuiteConsumer
from utils.thread_pool import VicThreadPoolExecutor, get_pool, safety_shutdown_pool
from utils.system import RUNNING_SUITES
from uuid import uuid4


def index(request):
    return render(request, "main/chat/index.html")


def room(request, room_name):
    return render(request, "main/chat/room.html", {"room_name": room_name})


class ChatConsumer(WebsocketConsumer):
    futures = list()
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive1(self, text_data, my_uuid):
        print(f"{time.time()}receive text_data = {text_data}")
        text_data_json = json.loads(text_data)
        time.sleep(5)
        user = SuiteConsumer.get_user(self)
        message = f"{user.username}: {text_data_json["message"]}"

        if user.username == "admin":
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {"type": "admin_message", "message": message}
            )
        else:
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {"type": "chat_message", "message": message}
            )
        RUNNING_SUITES.remove_suite(my_uuid)
        # 必须要return，Future才会标记为完成
        return

    def receive(self, text_data):
        my_uuid = uuid4()
        RUNNING_SUITES.add_suite(my_uuid, True)
        pool = get_pool()
        self.futures.append(pool.submit(self.receive1, text_data, my_uuid))
        print(f"====={my_uuid}=====")


    # Receive message from room group
    def chat_message(self, event):
        print(f"{event=}")
        message = event["message"]

        # Send message to WebSocket
        text_data = json.dumps({"message": message})
        print(f"{text_data}=")
        self.send(text_data)
        for f in self.futures:
            print(f"============={f=}=====================")

            print("Future 是否已完成:", f.done())  # 检查是否已完成
            print("Future 是否处于等待状态:", f.running())  # 检查是否处于等待状态
            print("Future 是否已取消:", f.cancelled())  # 检查是否已取消
        safety_shutdown_pool()

    def admin_message(self, event):
        message = event["message"]
        text_data = json.dumps({"message": f"管理员信息！{message}"})
        self.send(text_data)
