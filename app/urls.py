from django.urls import include, path
from rest_framework import routers

from app.views import *

router = routers.DefaultRouter()
router.register(r'user', UserViewset)
router.register(r'community',CommunityViewset)
router.register(r'article',ArticleViewset)
router.register(r'comment',CommentViewset)
router.register(r'chat',ChatViewset)
router.register(r'notification',NotificationViewset)
router.register(r'favourite',FavouriteViewset)
router.register(r'subscribe',SubscribeViewset)
router.register(r'feed',SocialPostViewset)
router.register(r'feedcomment',SocialPostCommentViewset)
router.register(r'follow',FollowViewset)

urlpatterns = [
    path("",include(router.urls)),
]