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
router.register(r'rating',ArticleRatingViewset)
router.register(r'subscribe',SubscribeViewset)
router.register(r'feed',SocialPostViewset)
router.register(r'feedcomment',SocialPostCommentViewset)
router.register(r'follow',FollowViewset)
router.register(r'message',PersonalMessageViewset)

urlpatterns = [
        path("",include(router.urls)),
    #path('', index, name='index'),
    # path('login', ManagerSigninView.as_view()),
    # path('register', ManagerSignupView.as_view()),
    # path('forgetPassword', ManagerForgetPassword.as_view()),
    # path('resetPassword', ManagerResetPassword.as_view()),
    # path('logout', ManagerLogoutView.as_view()),
    # path('venues', ManagerVenueView.as_view()),
    # path('venues/<str:venue>', ManagerSingleVenueView.as_view()),
    # path('venues/<str:venue>/<str:paper>', ManagerResearchPaperView.as_view()),
    # path('venues/<str:venue>/<str:paper>/all', ManagerVenuesResearchPaperView.as_view()),
    # path('paper/<str:paper>/comments', ManagerCommentsView.as_view()),
    # path("profile/<str:user>", ManagerUserView.as_view()),
    # path('review/<int:comment>/<str:data>', ManagerCommentLikeView.as_view()),
    # path('chat/<str:paper>/messages', ManagerChatView.as_view()),
    # path('subscribe/<str:venue>', ManagerSubscribeView.as_view()),
    # path('notifications', ManagerNotificationsView.as_view()),
    # path('search', ManagerSearchView.as_view()),
    # path('logout', ManagerLogoutView.as_view()),
]