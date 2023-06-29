from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<article_name>\w+)/$', consumers.ChatConsumer.as_asgi()), 
    # article name will be "article_<article_id>"
    # example: article_12 because id = 12
]