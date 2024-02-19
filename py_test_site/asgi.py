import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.conf import settings


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "py_test_site.settings")
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from main import routing  # routing必须在get_asgi_application()后执行

protocol_type_router = {"http": get_asgi_application()}
# AuthMiddlewareStack 在debug模式时会报错
# ...site-packages\django\utils\functional.py", line 309, in _setup
# NotImplementedError: subclasses of LazyObject must provide a _setup() method
if settings.DEBUG:
    protocol_type_router["websocket"] = URLRouter(routing.websocket_urlpatterns)
else:
    protocol_type_router["websocket"] = AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(routing.websocket_urlpatterns))
        )
application = ProtocolTypeRouter(protocol_type_router)