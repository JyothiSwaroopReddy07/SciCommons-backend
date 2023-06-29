"""
ASGI config for Website project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

# from app.consumers import ChatConsumer
import app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Website.settings')

# application = get_asgi_application()
application = ProtocolTypeRouter({
    "http":get_asgi_application(),
    "websocket":AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                app.routing.websocket_urlpatterns
            )
        )
    )
}) 

