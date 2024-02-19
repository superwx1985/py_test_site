import time

from django.shortcuts import render
import json
import asyncio
from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .websocket import SuiteConsumer
from django.contrib.auth.decorators import login_required
from channels.db import database_sync_to_async
from utils.thread_pool import VicThreadPoolExecutor, get_pool


@login_required
def index(request):
    return render(request, "main/chat/index.html")


@login_required
def room(request, room_name):
    return render(request, "main/chat/room.html", {"room_name": room_name})


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name

        # Join room group
        print(f"{self.channel_name=}")
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):

        print(f"{time.time()}receive text_data = {text_data}")
        # await do_something()
        await asyncio.sleep(5)
        text_data_json = json.loads(text_data)
        # 异步代码使用Django ORM
        user = await sync_to_async(SuiteConsumer.get_user)(self)
        # user = await database_sync_to_async(SuiteConsumer.get_user)(self)
        message = f"{user.username}: {text_data_json["message"]}"
        if user.username == "admin":
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "admin_message", "message": message}
            )
            return
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_message", "message": message}
        )

    # Receive message from room group
    async def chat_message(self, event):
        print(f"{event=}")
        message = event["message"]

        # Send message to WebSocket
        text_data = json.dumps({"message": message})
        print(f"{text_data}=")
        await self.send(text_data)

    async def admin_message(self, event):
        message = event["message"]
        text_data = json.dumps({"message": f"管理员信息！{message}"})
        await self.send(text_data)


def do_something(_time: int = 10):
    for i in range(_time):
        print(i)
        time.sleep(1)
