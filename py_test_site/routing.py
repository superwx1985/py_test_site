from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.conf.urls import url
from django.urls import path


from main.views import general

websocket_urlpatterns = [
    # url(r'^ws/chat/(?P<room_name>[^/]+)/$', general.ChatConsumer),
    path('ws/chat/<str:room_name>/', general.ChatConsumer),
]

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns,
            )
    ),
})
