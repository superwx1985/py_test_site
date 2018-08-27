from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.conf.urls import url
from django.urls import path


from main.views import websocket

websocket_urlpatterns = [
    # url(r'^ws/chat/(?P<room_name>[^/]+)/$', general.ChatConsumer),
    path('ws/suite_execute/<int:suite_pk>/', websocket.SuiteConsumer, name='suite_execute'),
    path('ws/suite_execute_remote/', websocket.SuiteRemoteConsumer, name='suite_execute_remote'),
]

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns,
            )
    ),
})
