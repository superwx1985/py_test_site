from django.core.asgi import get_asgi_application
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()


from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
from main.views import websocket

websocket_urlpatterns = [
    # url(r'^ws/chat/(?P<room_name>[^/]+)/$', general.ChatConsumer),
    path('ws/suite_execute/<int:suite_pk>/', websocket.SuiteConsumer, name='suite_execute'),
    path('ws/suite_execute_remote/', websocket.SuiteRemoteConsumer, name='suite_execute_remote'),
]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
