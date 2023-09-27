from rest_framework import permissions

from app.models import *
from app.serializer import *

class UserPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        
        if view.action in ['list', 'retrieve', 'getUserArticles', 'getposts','followers', 'following']:
            return True
        
        if view.action in [
            'create', 'login', 'refresh_token',
            'forgot_password', 'reset_password',
            ]:
            return True
        elif view.action in [
             'update', 'partial_update', 'destroy',
            'change_password','getMyArticle', 'getMyArticles','getMyCommunity', 'messages'
            ]:
            return request.user.is_authenticated and request.user == obj
        else:
            return False
        

class GeneralPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        
        if view.action in ['list', 'retrieve']:
            return True
        
        elif view.action in ['create', 'update', 'destroy']:
            return request.user.is_authenticated
        
class CommunityPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        if view.action in ['retrieve', 'list', 'getArticles']:
            return True
        
        elif view.action in ['update', 'getMembers', 'addPublishedInfo', 'destroy'
                             , 'remove_member', 'promote_member', 'get_requests', 'approve_request']:
            admins = CommunityMember.objects.filter(community=obj,is_admin=True)
            if request.user in [ admin.user for admin in admins]:
                return True
            else:
                return False
        
        elif view.action in ['create', 'subscribe','unsubscribe', 'join_request']:
            return request.user.is_authenticated
        
        return obj.user == request.user
       
class ArticlePermission(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):

        if view.action in ['retrieve', 'list', 'getPublisherDetails','updateViews']:
            return True
        
        elif view.action in ['create', 'submit_article','favourite','unfavourite', 'favourites']:
            return request.user.is_authenticated
        
        elif view.action in ['approve_article']:
            member = ArticleModerator.objects.filter(article=obj.id,moderator__user=request.user,moderator__community=request.data['community']).first()
            if member is None:
                return False
            else:
                return True
        
        elif view.action in ['approve_review','reject_article']:
            admin = CommunityMember.objects.filter(user=request.user, community=request.data['community']).first()
            return admin.is_admin

        elif view.action in [ 'destroy', 'update','getPublished', 'getIsapproved','status']:
            if Author.objects.filter(User=request.user, article=obj).first():
                return True
            else:
                return False
        elif view.action in ['blockUser', 'unblockUser']:
            member = Article.objects.filter(id=obj.pk).first()
            if request.user in member["moderators"]:
                return True
            else:
                return False



class CommentPermission(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):

        if view.action in ['retrieve', 'list']:
            return True
        
        elif view.action in ['create', 'like']:
            return request.user.is_authenticated
        
        elif view.action in ['update', 'destroy']:
            return obj.User == request.user


class NotificationPermission(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        
        if view.action in ['retrieve', 'list']:
            return request.user.is_authenticated
        
        if view.action in ['destroy']:
            return obj.user == request.user
        
class FavouritePermission(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):

        if view.action in ['retrieve', 'list']:
            return True
        
        elif view.action in ['create', 'like']:
            return request.user.is_authenticated
        
        elif view.action == 'destroy':
            return obj.user == request.user
        
class SocialPostPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        if view.action in ['retrieve', 'list','getMyPosts']:
            return True
        
        elif view.action in ['create', 'like','unlike', 'bookmarks']:
            return request.user.is_authenticated
        
        elif view.action in ['destroy', 'update','bookmark','unbookmark']:
            return obj.user == request.user

class SocialPostCommentPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        if view.action in ['retrieve', 'list']:
            return True
        
        elif view.action in ['create', 'like', 'unlike']:
            return request.user.is_authenticated
        
        elif view.action in [ 'destroy', 'update']:
            return obj.user == request.user
        
class FollowPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        if view.action in ['retrieve', 'list']:
            return True
        
        elif view.action in ['create', 'like']:
            return request.user.is_authenticated
        
        elif view.action in ['destroy']:
            return obj.user == request.user

class MessagePermissions(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action in ["list", "retrive"]:
            if obj.sender == request.User or obj.receiver == request.user:
                return True
            else:
                return False

        elif view.action in ["destroy", "update"]:
            return obj.sender == request.user


class ArticleChatPermissions(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):

        if request.user in obj.article.blocked_users.all():
            return False
        
        if view.action in ["list", "retrive"]:
            if obj.sender == request.User or obj.receiver == request.user:
                return True
            else:
                return False

        elif view.action in ["destroy"]:
            if obj.sender == request.user:
                return True
            elif request.user in obj.article.moderator.all():
                return True
            else:
                return False

        elif view.action in ["update"]:
            if obj.sender == request.user:
                return True
            else:
                return False