from django.urls import path, re_path
from main.views import websocket, chat, chat_sync

websocket_urlpatterns = [
    # url(r'^ws/chat/(?P<room_name>[^/]+)/$', general.ChatConsumer),
    path('ws/suite_execute/<int:suite_pk>/', websocket.SuiteConsumer.as_asgi(), name='suite_execute'),
    path('ws/suite_execute_remote/', websocket.SuiteRemoteConsumer.as_asgi(), name='suite_execute_remote'),
    re_path(r"ws/chat/(?P<room_name>\w+)/$", chat.ChatConsumer.as_asgi()),
    re_path(r"ws/chat_sync/(?P<room_name>\w+)/$", chat_sync.ChatConsumer.as_asgi()),
]
