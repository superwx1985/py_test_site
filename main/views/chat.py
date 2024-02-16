from django.shortcuts import render
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer


def index(request):
    return render(request, "main/chat/index.html")


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
        print(f"receive text_data = {text_data}")
        text_data_json = json.loads(text_data)
        username = f"{self.scope.get("user", "N/A")}"
        message = f"{username}: {text_data_json["message"]}"
        if username == "admin":
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
