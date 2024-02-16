from django.shortcuts import render
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


def index(request):
    return render(request, "main/chat/index.html")


def room(request, room_name):
    return render(request, "main/chat/room.html", {"room_name": room_name})


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name

        # Join room group
        print(f"{self.channel_name=}")
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
    def receive(self, text_data):
        print(f"receive user = {self.scope.get("user", "N/A")}")
        text_data_json = json.loads(text_data)
        username = f"{self.scope.get("user", "N/A")}"
        message = f"{username}: {text_data_json["message"]}"
        if username == "admin":
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {"type": "admin_message", "message": message}
            )
            return
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat_message", "message": message}
        )

    # Receive message from room group
    def chat_message(self, event):
        print(f"{event=}")
        message = event["message"]

        # Send message to WebSocket
        text_data = json.dumps({"message": message})
        print(f"{text_data}=")
        self.send(text_data)

    def admin_message(self, event):
        message = event["message"]
        text_data = json.dumps({"message": f"管理员信息！{message}"})
        self.send(text_data)
