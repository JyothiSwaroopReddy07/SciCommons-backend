import random
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework.decorators import action
from rest_framework import parsers, viewsets, permissions, status
from rest_framework.response import Response
from django.core.mail import send_mail
from django.contrib import messages
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.db.models import Q,Count,Subquery, OuterRef
from django.db.models.functions import Coalesce
from app.models import *
from app.serializer import *
from app.permissions import *
from app.filters import *
from rest_framework import filters
from django_filters import rest_framework as django_filters 

class UserViewset(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [UserPermission]
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    http_method_names = ['get','post','put','delete']

    search_fields = ['username', 'email']
    action_serializers = {
        'login':LoginSerializer,
        'create':UserCreateSerializer,
        'list': UserSerializer,
        'update':UserUpdateSerializer,
        'forgot_password':ForgotPasswordSerializer,
        'reset_password':ResetPasswordSerializer,
        'get_current_user':UserSerializer,
        'getMyArticles':AuthorSerializer,
        'getMyArticle':AuthorSerializer,
        'getUserArticles':UserSerializer,
        'getposts': SocialPostSerializer,
        'follow': FollowSerializer,
        'unfollow': FollowSerializer,
        'followers': FollowersSerializer,
        'following': FollowingSerializer,
        'myactivity': UserActivitySerializer,
        'verifyrequest': ForgotPasswordSerializer,
        'verifyemail': VerifySerializer,
    }


    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)

    def get_authenticated_user(self):
        user = get_object_or_404(self.queryset, pk=self.request.user.pk)
        self.check_object_permissions(self.request, user)
        return user

    def list(self, request):

        response = super(UserViewset, self).list(request)

        return Response(data={"success": response.data})
    
    def retrieve(self, request, pk):

        response = super(UserViewset, self).retrieve(request,pk=pk)

        return Response(data={"success": response.data})

    def create(self, request):
        super(UserViewset, self).create(request)

        return Response(data={"success": "User successfully added"})


    def update(self, request, pk):

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(data={"success":serializer.data})


    def destroy(self, request, pk ):

        super(UserViewset, self).destroy(request,pk=pk)

        return Response(data={"success": "User successfully deleted"})

    @action(methods=['post'], detail=False, permission_classes=[permissions.AllowAny,])
    def login(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response(data={"success":serializer.data})

    @action(methods=['get'], detail=False, url_path="articles", permission_classes=[permissions.IsAuthenticated,])
    def getMyArticles(self, request):
        authors = Author.objects.filter(User_id=request.user.id)
        articles = Article.objects.filter(author__in=authors)
        article_serializer = ArticlelistSerializer(articles, many=True, context={'request':request})

        return Response(data={"success": article_serializer.data})
    
    @action(methods=['get'], detail=False, url_path="articles/(?P<articleId>.+)", permission_classes=[permissions.IsAuthenticated,])
    def getMyArticle(self, request,articleId):
        authors = Author.objects.filter(User_id=request.user.id)
        articles = Article.objects.filter(author__in=authors,id=articleId)
        article_serializer = ArticleGetSerializer(articles, many=True, context={'request':request})

        return Response(data={"success": article_serializer.data})
    
    @action(methods=['get'], detail=False, url_path="(?P<username>.+)/posts", permission_classes=[permissions.IsAuthenticated])
    def getposts(self, request, username):
        instance = User.objects.filter(username=username).first()
        queryset = SocialPost.objects.filter(user_id=instance.id)
        serializer = SocialPostListSerializer(data=queryset, many=True, context={'request': request})
        serializer.is_valid()
        posts = serializer.data
        return Response(data={"success": posts})
    
    @action(methods=['get'], detail=False, url_path="(?P<username>.+)/articles", permission_classes=[permissions.IsAuthenticated])
    def getUserArticles(self, request, username):
        user = User.objects.filter(username=username).first()
        queryset = Author.objects.filter(User_id=user.id)
        articles = Article.objects.filter(author__in=queryset)
        serializer = ArticlelistSerializer(articles, many=True, context={'request':request})
        articles = serializer.data
        return Response(data={"success": articles})

    @action(methods=['get'], detail=False,permission_classes=[permissions.IsAuthenticated,])
    def get_current_user(self, request, pk=None):
        """
        get logged in user
        """
        serializer = self.get_serializer(self.get_authenticated_user())
        return Response(data={"success": serializer.data})

    @action(methods=['post'],url_path="verifyrequest", detail=False,permission_classes=[permissions.AllowAny,])
    def verifyrequest(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = random.randint(100000, 999999)
        user = User.objects.filter(email=serializer.data['email']).first()
        if user is None:
            return Response(data={"error": "Please Enter valid email address!!!"}, status=status.HTTP_400_BAD_REQUEST)
        verify = EmailVerify.objects.create(user=user, otp=otp)
        email_from = settings.EMAIL_HOST_USER
        email_subject = "Email Verification"
        email_body = "Your OTP is " + str(otp)
        send_mail(email_subject, email_body, email_from, [serializer.data['email']], fail_silently=False)
        return Response(data={"success": "code sent to your email"})
    
    @action(methods=['post'],url_path="verify_email",detail=False,permission_classes=[permissions.AllowAny,])
    def verifyemail(self,request):
        otp = request.data.get('otp')
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()
        if user is None:
            return Response(data={"error": "Please enter correct mail address"}, status=status.HTTP_400_BAD_REQUEST)
        res = EmailVerify.objects.filter(otp=otp,user=user).first()
        if res is None:
            res1 = EmailVerify.objects.filter(user=user).first()
            res1.delete()
            return Response(data={"error": "Otp authentication failed.Please generate new Otp!!!"}, status=status.HTTP_400_BAD_REQUEST)
        res.delete()
        user.email_verified = True
        user.save()
        return Response(data={"success": "Email Verified Successfully!!!"})

    @action(methods=['post'],url_path="forgot_password", detail=False,permission_classes=[permissions.AllowAny,])
    def forgot_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        otp = random.randint(100000, 999999)

        user = User.objects.filter(email=serializer.data['email']).first()
        if user is None:
            return Response(data={"error": "Please enter a valid email address"}, status=status.HTTP_400_BAD_REQUEST)
        forget = ForgetPassword.objects.create(user=user, otp=otp)
        forget.save()

        email_from = settings.EMAIL_HOST_USER
        email_subject = "Reset Password"
        email_body = "You have forgot you account password. Your OTP is " + str(otp)
        send_mail(email_subject, email_body, email_from, [serializer.data['email']], fail_silently=False)
        return Response(data={"success": "code sent to your email"})

        
    @action(methods=['post'],url_path="reset_password", detail=False,permission_classes=[permissions.AllowAny,])
    def reset_password(self, request):
        otp = request.data.get('otp')
        email = request.data.get('email')
        password = request.data.get('password')
        password2 = request.data.get('password2')
        user = User.objects.filter(email=email).first()
        if user is None:
            return Response(data={"error": "Please enter valid email address"}, status=status.HTTP_400_BAD_REQUEST)
        forget = ForgetPassword.objects.filter(otp=otp, user=user).first()
        if forget is None:
            return Response(data={"error":"Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
                
        user = forget.user
        if password == password2:
            user.set_password(password)
            user.save()
            forget.delete()
            return Response(data={"success": "password reset successfully"})
        else:
            messages.error(request, 'Password not matching.')
            return Response(data={"error": "Password not matching"}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(methods=['post'],url_path='follow', detail=False, permission_classes=[permissions.IsAuthenticated])
    def follow(self, request):
        instance = User.objects.filter(id=request.data["followed_user"]).first()
        member = Follow.objects.filter(followed_user=instance, user=request.user).first()
        if member is not None:
            return Response(data={"error":"Already following!!!"})
        Follow.objects.create(followed_user=instance, user=request.user)
        return Response(data={"success":"followed!!!"})

    @action(methods=['post'],url_path='unfollow', detail=False, permission_classes=[permissions.IsAuthenticated])
    def unfollow(self, request):
        instance = User.objects.filter(id=request.data["followed_user"]).first()
        member = Follow.objects.filter(followed_user=instance,user=request.user).first()
        if member is not None:
            member.delete()
            return Response(data={"success":"UnFollowed!!!"})
        else:
            return Response(data={"error":"Did not Follow!!!"})
    
    @action(methods=['get'],url_path='myactivity',detail=False,permission_classes=[permissions.IsAuthenticated])
    def myactivity(self,request):
        activities = UserActivity.objects.filter(user_id=request.user)
        serializer = UserActivitySerializer(activities,many=True)
        return Response(data={"success":serializer.data})
        
    @action(methods=['get'],url_path="followers", detail=False,permission_classes=[permissions.IsAuthenticated])
    def followers(self,request):
        instance = User.objects.filter(username=request.query_params.get("username")).first()
        member = Follow.objects.filter(followed_user=instance)
        serializer = FollowersSerializer(member,many=True,context={'request':request})
        return Response(data={"success": serializer.data})

    @action(methods=['get'],url_path="following", detail=False,permission_classes=[permissions.IsAuthenticated])
    def following(self,request):
        instance = User.objects.filter(username=request.query_params.get("username")).first()
        member = Follow.objects.filter(user=instance)
        serializer = FollowingSerializer(member,many=True,context={'request':request})
        return Response(data={"success": serializer.data})

class CommunityViewset(viewsets.ModelViewSet):
    queryset = Community.objects.all()
    queryset2 = CommunityMeta.objects.all()
    queryset3 = CommunityMember.objects.all()
    permission_classes = [CommunityPermission]
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = CommunitySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    http_method_names = ['post', 'get', 'put', 'delete']
    lookup_field = "Community_name"

    search_fields = ['Community_name']
    
    action_serializers = {
        "create":CommunityCreateSerializer,
        "update":CommunityUpdateSerializer,
        "promote_member":PromoteSerializer,
        "addPublishedInfo":ArticlePostPublishSerializer,
        "getMembers":CommunityMemberSerializer,
        "getArticles": CommunityMetaArticlesSerializer,
        "list": CommunitylistSerializer,
        "retrieve": CommunityGetSerializer,
        "join_request":JoinRequestSerializer,
        "get_requests":CommunityRequestGetSerializer,
        "approve_request":ApproverequestSerializer,
        "subscribe": SubscribeSerializer,
        "unsubscribe": SubscribeSerializer,
        'mycommunity': CommunitySerializer,
    }
    
    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)
    
    def list(self, request):

        response = super(CommunityViewset, self).list(request)

        return Response(data={"success":response.data})
    
    def retrieve(self, request, Community_name):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(CommunityViewset, self).retrieve(request,Community_name=Community_name)

        return Response(data={"success":response.data})

    def create(self, request):
        
        member = self.queryset.filter(user=request.user).first()
        if member is not None:
            return Response(data={"error": "You already created a community.You can't create another community!!!"}, status=status.HTTP_400_BAD_REQUEST)
        super(CommunityViewset, self).create(request)

        return Response(data={"success": "Community successfully added"})


    def update(self, request, Community_name):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(data={"success": serializer.data})


    def destroy(self, request, Community_name ):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        super(CommunityViewset, self).destroy(request,Community_name=Community_name)

        return Response(data={"success": "community successfully deleted"})

    @action(methods=['GET'], detail=False, url_path='(?P<Community_name>.+)/articles', permission_classes=[CommunityPermission])
    def getArticles(self, request, Community_name):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = self.queryset2.filter(community__Community_name=Community_name)
        serializer = CommunityMetaArticlesSerializer(data=response, many=True)
        serializer.is_valid()
        articles = serializer.data
        return Response(data={"success": articles})

    @action(methods=['get'], detail=False, url_path="mycommunity", permission_classes=[permissions.IsAuthenticated,])
    def getMyCommunity(self, request):
        member = CommunityMember.objects.filter(user=request.user,is_admin=True).first()
        instance = Community.objects.filter(id=member.community.id)
        serializer = CommunitySerializer(data=instance, many=True)
        serializer.is_valid()
        community = serializer.data
        return Response(data={"success": community[0]})
    
    @action(methods=['POST'], detail=False, url_path='(?P<Community_name>.+)/article/(?P<article_id>.+)/publish',permission_classes=[CommunityPermission])
    def addPublishedInfo(self, request, Community_name, article_id):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        article = Article.objects.filter(article_id=article_id).first()
        if(article["published"] != Community_name):
            return Response(data={"error": "This action can't be performed"})
        else:
            data = request.data
            serializer = ArticlePostPublishSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data={"success": "You added the license,Article file to the published Article"})
    
    @action(methods=['GET'],detail=False,url_path='(?P<Community_name>.+)/members',permission_classes=[CommunityPermission])
    def getMembers(self, request, Community_name):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = self.queryset3.filter(community=obj)
        serializer = self.get_serializer(data=response, many=True)
        serializer.is_valid()
        users = serializer.data
        return Response(data={"success": users})
    
    @action(methods=['POST'],detail=False, url_path='(?P<Community_name>.+)/promote_member',permission_classes=[CommunityPermission]) 
    def promote_member(self, request, Community_name):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        member = User.objects.filter(username=request.data["username"]).first()
        if member is None:
            return Response(data={"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        admin = Community.objects.filter(user_id=member.id).first()
        if admin is not None:
            return Response(data={"error": "You cant perform this action"},status=status.HTTP_404_NOT_FOUND)
        request.data["user_id"] = member.id
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(data={"success": "member promoted successfully"})
    
    @action(methods=['DELETE'],detail=False, url_path='(?P<Community_name>.+)/remove_member/(?P<user_id>.+)',permission_classes=[CommunityPermission]) 
    def remove_member(self, request, Community_name, user_id):
        
        obj = self.get_object()
        self.check_object_permissions(request,obj)

        admin = Community.objects.filter(user_id=user_id).first()
        if admin is not None:
            return Response(data={"error": "You cant perform this action"},status=status.HTTP_404_NOT_FOUND)
        
        try:
            member = CommunityMember.objects.filter(community=obj, user_id=user_id).first()
            emails = []
            emails.append(member.user.email)
            if member is None:
                return Response(data={"error": "Not member of community"}, status=status.HTTP_404_NOT_FOUND)
            member.delete()
            send_mail(f'you are removed from {obj}',f'You have been removed from {obj}.Due to inappropriate behaviour', settings.EMAIL_HOST_USER , emails, fail_silently=False)

            
        except Exception as e:
            return Response(data={'error': 'unable to delete it.Please try again later!!!'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(data={"success": "member removed successfully"})
    
    
    @action(methods=['POST'],detail=False, url_path='(?P<Community_name>.+)/join_request',permission_classes=[CommunityPermission])
    def join_request(self, request, Community_name):

        obj = self.get_object()
        data = request.data
        data["community"] = obj.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(data={"success":serializer.data})

    @action(methods=['GET'],detail=False, url_path='(?P<Community_name>.+)/get_requests',permission_classes=[CommunityPermission])
    def get_requests(self, request, Community_name):

        obj = self.get_object()
        requests = CommunityRequests.objects.filter(community=obj)
        serializer = self.get_serializer(requests, many=True)

        return Response(data={"success":serializer.data})

    @action(methods=['POST'],detail=False, url_path='(?P<Community_name>.+)/approve_request',permission_classes=[CommunityPermission])
    def approve_request(self, request, Community_name):

        obj = self.get_object()
        joinrequest = CommunityRequests.objects.get(community=obj)

        serializer = self.get_serializer(joinrequest, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if serializer.data['status']=="approved":
            obj.members.add(serializer.data['user'])

        joinrequest.delete()

        return Response(data={"success":serializer.data})
    
    @action(methods=['post'], detail=False,url_path='(?P<Community_name>.+)/subscribe', permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, Community_name):
        member = Subscribe.objects.filter(community__Community_name=Community_name, user=request.user).first()
        if member is not None:
            return Response(data={"error":"Already Subscribed!!!"})
        instance = Community.objects.filter(Community_name=Community_name).first()
        Subscribe.objects.create(community=instance, user=request.user)
        return Response(data={"success":"Subscribed!!!"})

    @action(methods=['post'], detail=False,url_path='(?P<Community_name>.+)/unsubscribe', permission_classes=[permissions.IsAuthenticated])
    def unsubscribe(self, request,Community_name):
        member = Subscribe.objects.filter(community__Community_name=Community_name,user=request.user).first()
        if member is not None:
            member.delete()
            return Response(data={"success":"Unsubscribed!!!"})
        else:
            return Response(data={"error":"Did not Subscribe!!!"})

    
class ArticleViewset(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    permission_classes = [ArticlePermission]
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter,filters.OrderingFilter]
    filterset_class = ArticleFilter
    http_method_names = ['post', 'get', 'put', 'delete']
    search_fields = ['article_name', 'keywords', 'authorstring']
    
    action_serializers = {
        "list": ArticlelistSerializer,
        "retrieve":ArticleGetSerializer,
        "create":ArticleCreateSerializer,
        "approve_article":ApproveSerializer,
        "approve_review":InReviewSerializer,
        "reject_article": RejectSerializer,
        "submit_article":SubmitArticleSerializer,
        "update": ArticleUpdateSerializer,
        "getIsapproved": CommunityMetaApproveSerializer,
        "getPublisherDetails": ArticlePublisherSerializer,
        "getPublished": ArticlePublishSelectionSerializer,
        "status": StatusSerializer,
        "updateViews": ArticleViewsSerializer,
        "block_user": ArticleBlockUserSerializer,
        "favourite": FavouriteCreateSerializer,
        "unfavourite": FavouriteSerializer,
        "favourites": FavouriteSerializer

    }
    
    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)
    
    def get_queryset(self):
        queryset = self.queryset
        return queryset

    
    def list(self, request):
        response = super(ArticleViewset, self).list(request)

        return Response(data={"success":response.data})
    
    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(ArticleViewset, self).retrieve(request,pk=pk)

        return Response(data={"success":response.data})

    def create(self, request):
        name = request.data['article_name']
        name = name.replace(' ','_')
        article = self.queryset.filter(article_name=name).first()
        if article is not None:
            return Response(data={"error": "Article with same name already exists!!!"}, status=status.HTTP_400_BAD_REQUEST)
        response = super(ArticleViewset, self).create(request)
    
        return Response(data={"success": "Article successfully submitted"})


    def update(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        article = Article.objects.filter(id=pk).first()
        response = ArticleGetSerializer(article,context={'request': request})
        return Response(data={"success": "Article successfully updated", "data":response.data})

    def destroy(self, request, pk ):
        obj = self.get_object()
        self.check_object_permissions(request,obj)

        super(ArticleViewset, self).destroy(request,pk=pk)

        return Response(data={"success": "Article successfully deleted"})

    @action(methods=['get'], detail=False, url_path='(?P<pk>.+)/isapproved', permission_classes=[ArticlePermission])
    def getIsapproved(self, request, pk):
        '''
        retrieve the status of article in different communities with accepted status
        '''
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = CommunityMeta.objects.filter(article_id=pk)
        serializer = CommunityMetaApproveSerializer(data=response, many=True)
        serializer.is_valid()
        communities = serializer.data
        return Response(data={"success": communities})

    @action(methods=['post'],detail=False, url_path='(?P<pk>.+)/approve_for_review', permission_classes=[ArticlePermission])
    def approve_review(self, request, pk):
        '''
            article approved for review process
        '''
        member = Community.objects.filter(Community_name=request.data["community"]).first()
        request.data["community"] = member.id
        obj = self.get_object()
        serializer = self.get_serializer(obj,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={"success":"review process started successfully"})

    @action(methods=['get'], detail=False, url_path='(?P<pk>.+)/publisher', permission_classes=[ArticlePermission])
    def getPublisherDetails(self, request, pk):
        '''
       get published information of article
        '''
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = Article.objects.filter(id=pk)
        serializer = ArticlePublisherSerializer(data=response, many=True)
        serializer.is_valid()
        publisher = serializer.data
        if publisher[0]["published"] is not None:
            return Response(data={"success": publisher[0]})
        else:
            return Response(data={"error": "This article is still not published in any community"})
    
    @action(methods=['post'], detail=False, url_path='(?P<pk>.+)/publish', permission_classes=[ArticlePermission])
    def getPublished(self, request, pk):
        '''
        select a community for publication
        '''
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        data = request.data
        response = CommunityMeta.objects.filter(article_id=pk,community__Community_name=data["published"]).first()
        if response is None:
            return Response(data={"error": f'Article is not submitted to {data["published"]}'}) 
        serializer = CommunityMetaSerializer(data=response, many=True)
        serializer.is_valid()
        meta = serializer.data
        if meta[0]['status'] == 'accepted':
            data['Community_name'] = data['published']
            data['id'] = pk
            serializer = ArticlePublishSelectionSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(data={"success": f"You have chosen {data['Community_name']} to publish your article"})
        else:
            return Response(data={"error": "Article is still not approved by community"})        

    @action(methods=['get'], detail=False, url_path='favourites', permission_classes=[ArticlePermission])
    def favourites(self, request):
        favourites = Favourite.objects.filter(user=request.user).values_list('article', flat=True)
        posts = Article.objects.filter(id__in=favourites.all(),status="public")
        serializer = ArticlelistSerializer(posts, many=True, context={"request":request})
        return Response(data={"success":serializer.data})
        

    @action(methods=['post'],detail=False, url_path='(?P<pk>.+)/submit_article', permission_classes=[ArticlePermission])
    def submit_article(self, request, pk):
        '''
        submit article to different communities
        '''
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        data = request.data
        data['article_id']=pk
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(data={"success": "Article submited successfully for reviewal process!!!"})

    @action(methods=['put'], detail=False, url_path='(?P<pk>.+)/updateviews',permission_classes=[ArticlePermission])
    def updateViews(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        response = self.queryset.get(id=pk)
        serializer = ArticleViewsSerializer(response)
        article = serializer.data
        article['views'] += 1
        serializer = ArticleViewsSerializer(response, data=article)
        if serializer.is_valid():
            serializer.save() 
            return Response(data={"success": "Added a view to the article"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
    @action(methods=['post'],detail=False, url_path='(?P<pk>.+)/approve_article', permission_classes=[ArticlePermission])    
    def approve_article(self, request, pk):
        '''
        admin approve article and select reviewers and moderators
        '''
        member = Community.objects.filter(Community_name=request.data["community"]).first()
        request.data["community"] = member.id
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        serializer = self.get_serializer(obj ,data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(data={"success":"article approved"})
    
    @action(methods=['post'], detail=False,url_path="favourite", permission_classes=[FavouritePermission])
    def favourite(self, request):
        post = Favourite.objects.filter(article_id=request.data["article"], user=request.user).first()
        if post is not None:
            return Response(data={"error":"Already added to Favourites!!!"})
        Favourite.objects.create(article_id=request.data["article"], user=request.user)
        return Response(data={"success":"Favourite added!!!"})

    @action(methods=['post'], detail=False,url_path="unfavourite", permission_classes=[FavouritePermission])
    def unfavourite(self, request):
        member = Favourite.objects.filter(article_id=request.data["article"],user=request.user).first()
        if member is not None:
            member.delete()
            return Response(data={"success":"Favourite Removed!!!"})
        else:
            return Response(data={"error":"Favourite not found!!!"})
    
    @action(methods=['post'],detail=False, url_path='(?P<pk>.+)/reject_article', permission_classes=[ArticlePermission])    
    def reject_article(self, request, pk):
        '''
        reject the article
        '''
        member = Community.objects.filter(Community_name=request.data["community"]).first()
        request.data["community"] = member.id
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        serializer = self.get_serializer(obj ,data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(data={"success":"article rejected"})
    
    @action(methods=['post'],detail=False, url_path='(?P<pk>.+)/status', permission_classes=[ArticlePermission])
    def status(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        try:
            stat = request.data.get("status", None)
            if stat is None:
                return Response(data={"error":"status can't be None"}, status=status.HTTP_400_BAD_REQUEST)
                
            article = Article.objects.filter(id=pk).first()
            if article is None:
                return Response(data={"error":"article not exist"}, status=status.HTTP_404_NOT_FOUND)
            article.status = stat
            article.save()
            return Response(data={"success":f"article status changed to {stat}"})
        
        except Exception as e:
            return Response(data={"error":e}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=['post'],detail=False, url_path='(?P<pk>.+)/block_user', permission_classes=[ArticlePermission])
    def block_user(self, request, pk):
        obj = self.get_object()

        serialzer = self.get_serializer(obj, data=request.data, partial=True)
        serialzer.is_valid(raise_execption=True)
        serialzer.save()
        return Response(data={"success":f"user blocked successfully"})
      
class CommentViewset(viewsets.ModelViewSet):
    queryset = CommentBase.objects.all()
    queryset2 = LikeBase.objects.all()
    permission_classes = [CommentPermission]    
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = CommentSerializer
    # filter_backends = [DjangoFilterBackend,filters.OrderingFilter]
    # filterset_class = CommentFilter
    http_method_names = ['post', 'get', 'put', 'delete']
    
    action_serializer = {
        "list": CommentlistSerializer,
        "create":CommentCreateSerializer,
        "update":CommentUpdateSerializer,
        "retrieve": CommentSerializer,
        "destroy": CommentSerializer,
        "like":LikeSerializer
    }
    
    def get_serializer_class(self):
        return self.action_serializer.get(self.action, self.serializer_class)
    
    def get_queryset(self):
        article = self.request.query_params.get("article", None)
        tag = self.request.query_params.get("Community_name",None)
        Type = self.request.query_params.get("Type",None)
        comment_type = self.request.query_params.get("comment_type",None)
        parent_comment = self.request.query_params.get("parent_comment",None)
        version = self.request.query_params.get("version",None)
        if article is not None:
            if Type is not None:
                if tag is not None:
                    if comment_type is not None:
                        qs = self.queryset.filter(article=article,tag=tag,Type=Type,comment_type=comment_type,parent_comment=parent_comment,version=version)
                    else:
                        qs = self.queryset.filter(article=article,tag=tag,Type=Type,parent_comment=parent_comment,version=version)
                else:
                    if comment_type is not None:
                        qs = self.queryset.filter(article=article,Type=Type,comment_type=comment_type,parent_comment=parent_comment,version=version)
                    else:
                        qs = self.queryset.filter(article=article,Type=Type,parent_comment=parent_comment,version=version)
            else:
                if tag is not None:
                    if comment_type is not None:
                        qs = self.queryset.filter(article=article,tag=tag,comment_type=comment_type,parent_comment=parent_comment,version=version)
                    else:
                        qs = self.queryset.filter(article=article,tag=tag,parent_comment=parent_comment,version=version)
                else:
                    if comment_type is not None:
                        qs = self.queryset.filter(article=article,comment_type=comment_type,parent_comment=parent_comment,version=version)
                    else:
                        qs = self.queryset.filter(article_id=article,parent_comment=parent_comment,version=version)
        else:
            qs = []
            
        return qs
    
    def list(self, request):
        
        response = super(CommentViewset, self).list(request)

        return Response(data={"success":response.data})
    
    def retrieve(self, request, pk):

        response = super(CommentViewset, self).retrieve(request,pk=pk)

        return Response(data={"success":response.data})

    def create(self, request):
        if request.data["parent_comment"] or request.data["version"]:
            request.data["Type"] = "comment"

        if request.data["Type"] == 'decision':
            moderators_arr = [moderator for moderator in ArticleModerator.objects.filter(article=request.data["article"],moderator__user = request.user)]
            if len(moderators_arr)>0:
                if self.queryset.filter(article=request.data["article"],User=request.user,Type="decision").first():
                    return Response(data={"error": "You have already made decision!!!"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    response = super(CommentViewset, self).create(request)
                    member = CommentBase.objects.filter(id=response.data.get("id")).first()
                    created = CommentSerializer(instance=member, context={'request': request})
                    return Response(data={"success":"Decision successfully added", "comment": created.data})
            
            else: 
                return Response(data={"error": "You can't write a decision on the article!!!"}, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.data['Type'] == 'review':
            author = Author.objects.filter(User=request.user,article=request.data["article"]).first()
            if author is not None:
                return Response(data={"error": "You are Author of Article.You can't submit a review"}, status=status.HTTP_400_BAD_REQUEST)
            
            c = ArticleModerator.objects.filter(article=request.data["article"],moderator__user = request.user).count()
            if c > 0:
                return Response(data={"error": "You can't make a review over article"}, status=status.HTTP_400_BAD_REQUEST)
            
            count = CommentBase.objects.filter(article=request.data["article"],User=request.user,tag=request.data['tag'],Type='review').count()
            if count == 0:
                response = super(CommentViewset, self).create(request)
                member = CommentBase.objects.filter(id=response.data.get("id")).first()
                created = CommentSerializer(instance=member, context={'request':request})
                return Response(data={"success":"Review successfully added", "comment": created.data})
            
            else: 
                return Response(data={"error":"Review already added by you!!!"}, status=status.HTTP_400_BAD_REQUEST)
                
        else:
            if request.data['Type'] == 'comment' and (request.data['parent_comment'] or request.data['version']) is None:
                return Response(data={"error":"Comment must have a parent instance"}, status=status.HTTP_400_BAD_REQUEST)
            
            response = super(CommentViewset, self).create(request)
            member = CommentBase.objects.filter(id=response.data.get("id")).first()
            created = CommentSerializer(instance=member, context={'request': request})
            return Response(data={"success":"Comment successfully added","comment": created.data})


    def update(self, request, pk):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(data={"success":serializer.data})


    def destroy(self, request, pk ):
        
        super(CommentViewset, self).destroy(request,pk=pk)

        return Response(data={"success":"Comment successfully deleted"})
    
    @action(methods=['post'], detail=False, permission_classes=[permissions.IsAuthenticated])
    def like(self, request):
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = LikeBase.objects.filter(user=request.user, post=serializer.data['post']).first()
        comment = CommentBase.objects.filter(id=serializer.data['post']).first()
        if comment.User == request.user:
            return Response(data={'error': "you can't rate your comment"}, status=status.HTTP_400_BAD_REQUEST)
        handle = HandlersBase.objects.filter(User=request.user, article=comment.article).first()
        if handle is None: 
            handle = HandlersBase.objects.create(User=request.user, article=comment.article, handle_name=fake.name())
            handle.save()
        handle = HandlersBase.objects.filter(User=self.request.user,article=comment.article).first()
        if member is not None:
            rank = Rank.objects.filter(user=comment.User).first()
            rank.rank -= member.value
            rank.rank += serializer.data['value']
            member.value = serializer.data['value']
            member.save()
            rank.save()
            return Response({'success': 'Comment rated successfully.'})
        else :

            like = LikeBase.objects.create(user=self.request.user, post=comment, value=serializer.data['value'])
            like.save()
                
            rank = Rank.objects.filter(user=comment.User).first()
            if rank:
                rank.rank += serializer.data['value']
                rank.save()

            else:
                rank = Rank.objects.create(user=self.request.user, rank=serializer.data['value'])
                rank.save()
            
            return Response({'success': 'Comment rated successfully.'})
            
    

class NotificationViewset(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    permission_classes = [NotificationPermission]    
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = NotificationSerializer
    http_method_names = ['get','put', 'delete']
        
    def get_queryset(self):
        qs = self.queryset.filter(user=self.request.user).order_by('-date')
        return qs
    
    def list(self, request):
        response = super(NotificationViewset , self).list(request)
    
        return Response(data={"success":response.data})
    
    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(NotificationViewset, self).retrieve(request,pk=pk)
    
        return Response(data={"success":response.data})

    def update(self, request, pk):
        instance = Notification.objects.filter(id=pk).first()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(data={"success":"notification marked!!!"})
    
    def destroy(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(NotificationViewset, self).destroy(request, pk)
    
        return Response(data={"success":"Notification deleted successfully."})



class SocialPostViewset(viewsets.ModelViewSet):
    queryset = SocialPost.objects.all()
    permission_classes = [SocialPostPermission]    
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = SocialPostSerializer
    # filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # filterset_class = PostFilters
    http_method_names = ['get', 'post', 'delete', 'put']
    
    action_serializers = {
        "create": SocialPostCreateSerializer,
        "destroy": SocialPostSerializer,
        "retrieve": SocialPostGetSerializer,
        "list": SocialPostListSerializer,
        "update": SocialPostUpdateSerializer,
        "like": SocialPostLikeSerializer,
        "unlike": SocialPostLikeSerializer,
        "bookmark": SocialPostBookmarkSerializer,
        "unbookmark": SocialPostBookmarkSerializer,
        "bookmarks": SocialPostListSerializer,
    }
        
    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)
    
    def get_queryset(self):
        qs = self.queryset.order_by('-created_at').exclude(user=self.request.user)
        return qs
    
    def list(self, request):
        response = super(SocialPostViewset , self).list(request)
    
        return Response(data={"success":response.data})
    
    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(SocialPostViewset, self).retrieve(request,pk=pk)
    
        return Response(data={"success":response.data})
    
    
    def create(self, request):

        response = super(SocialPostViewset, self).create(request)
    
        return Response(data={"success":"Post Successfully added!!!"})
    
    def update(self, request, pk):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(data={"success":serializer.data})
    
    def destroy(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(SocialPostViewset, self).destroy(request, pk)
    
        return Response(data={"success":"Post Successfuly removed!!!"})
    
    @action(methods=['get'],detail=False,url_path="timeline", permission_classes=[SocialPostPermission])
    def timeline(self,request):
        following = Follow.objects.filter(user=request.user).values_list('followed_user', flat=True)
        posts = SocialPost.objects.filter(user__in=following.all())
        serializer = SocialPostListSerializer(posts, many=True,context={"request":request})
        return Response(data={"success":serializer.data})
    
    @action(methods=['get'],detail=False,url_path="bookmarks", permission_classes=[SocialPostPermission])
    def bookmarks(self,request):
        bookmarks = BookMark.objects.filter(user=request.user).values_list('post', flat=True)
        posts = SocialPost.objects.filter(id__in=bookmarks.all())
        serializer = SocialPostListSerializer(posts, many=True, context={"request":request})
        return Response(data={"success":serializer.data})

    @action(methods=['post'], detail=False,url_path="like", permission_classes=[SocialPostPermission])
    def like(self, request):

        post = SocialPostLike.objects.filter(post_id=request.data["post"], user=request.user).first()
        if post is not None:
            return Response(data={"error":"Already Liked!!!"})
        SocialPostLike.objects.create(post_id=request.data["post"], user=request.user)
        return Response(data={"success":"Liked!!!"})

    @action(methods=['post'], detail=False,url_path="unlike", permission_classes=[SocialPostCommentPermission])
    def unlike(self, request):

        member = SocialPostLike.objects.filter(post_id=request.data["post"],user=request.user).first()
        if member is not None:
            member.delete()
            return Response(data={"success":"DisLiked!!!"})
        else:
            return Response(data={"error":"Post not found!!!"})
    
    @action(methods=['post'], detail=False,url_path="bookmark", permission_classes=[SocialPostPermission])
    def bookmark(self, request):
        post = BookMark.objects.filter(post_id=request.data["post"], user=request.user).first()
        if post is not None:
            return Response(data={"error":"Already Bookmarked!!!"})
        BookMark.objects.create(post_id=request.data["post"], user=request.user)
        return Response(data={"success":"Bookmarked!!!"})

    @action(methods=['post'], detail=False,url_path="unbookmark", permission_classes=[SocialPostPermission])
    def unbookmark(self, request):
        member = BookMark.objects.filter(post_id=request.data["post"],user=request.user).first()
        if member is not None:
            member.delete()
            return Response(data={"success":"UnBookmarked!!!"})
        else:
            return Response(data={"error":"BookMark not found!!!"})



class SocialPostCommentViewset(viewsets.ModelViewSet):
    queryset = SocialPostComment.objects.all()
    permission_classes = [SocialPostCommentPermission]    
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = SocialPostCommentSerializer
    http_method_names = ['get', 'post', 'delete', 'put']
    
    action_serializers = {
        "create": SocialPostCommentCreateSerializer,
        "destroy": SocialPostCommentSerializer,
        "retrieve": SocialPostCommentListSerializer,
        "list": SocialPostCommentListSerializer,
        "update": SocialPostCommentUpdateSerializer,
        "like": SocialPostCommentLikeSerializer,
        "unlike": SocialPostCommentLikeSerializer
    }
        
    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)
    
    def get_queryset(self):
        post = self.request.query_params.get("post", None)
        comment = self.request.query_params.get("comment", None)
        if comment is not None:
            qs = self.queryset.filter(post_id = post,parent_comment_id=comment)
        elif post is not None:
            qs = self.queryset.filter(post_id=post).exclude(parent_comment__isnull=False)
        else:
            qs = []
        return qs
    
    def list(self, request):
        response = super(SocialPostCommentViewset , self).list(request)
    
        return Response(data={"success":response.data})
    
    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(SocialPostCommentViewset, self).retrieve(request,pk=pk)
    
        return Response(data={"success":response.data})
    
    
    def create(self, request):
        response = super(SocialPostCommentViewset, self).create(request)
        created = response.data
    
        return Response(data={"success":"Comment Successfully added!!!","comment": created})
    
    def update(self, request, pk):

        instance = SocialPostComment.objects.filter(id=pk).first()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(data={"success":serializer.data})
    
    def destroy(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(SocialPostCommentViewset, self).destroy(request, pk)
    
        return Response(data={"success":"Comment Successfuly removed!!!"})

    @action(methods=['post'], detail=False,url_path="like", permission_classes=[SocialPostCommentPermission])
    def like(self, request):
        if SocialPostCommentLike.objects.filter(comment_id=request.data["comment"], user=request.user).first() is not None:
            return Response(data={"error":"Already Liked!!!"})
        SocialPostCommentLike.objects.create(comment_id=request.data["comment"], user=request.user)
        return Response(data={"success":"Liked!!!"})

    @action(methods=['post'], detail=False,url_path="unlike", permission_classes=[SocialPostCommentPermission])
    def unlike(self, request):
        comment = SocialPostCommentLike.objects.filter(comment_id=request.data["comment"],user=request.user).first()
        if comment is not None:
            comment.delete()
            return Response(data={"success":"DisLiked!!!"})
        else:
            return Response(data={"error":"Comment not found!!!"})
  
    


class ArticleChatViewset(viewsets.ModelViewSet):
    queryset = ArticleMessage.objects.all()
    permission_classes = [ArticleChatPermissions]
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = ArticleChatSerializer
    http_method_names = ["post", "get", "put", "delete"]

    action_serializer = {
                        "create": ArticleChatCreateSerializer,
                         "retrieve": ArticleChatSerializer,
                         "list": ArticleChatSerializer,
                         "update": ArticleChatUpdateSerializer,
                         "destroy": ArticleChatSerializer
                        }

    def get_serializer_class(self):
        return self.action_serializer.get(self.action, self.serializer_class)

    def get_queryset(self):
        article = self.request.query_params.get("article", None)
        if article is not None:
            qs = self.queryset.filter(article=article).order_by("-created_at")
            return qs
        return self.queryset

    def list(self, request):
        response = super(ArticleChatViewset, self).list(request)

        return Response(data={"success": response.data})

    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        response = super(ArticleChatViewset, self).retrieve(request, pk=pk)

        return Response(data={"success": response.data})

    def create(self, request):
        response = super(ArticleChatViewset, self).create(request)

        return Response(data={"success": response.data})

    def update(self, request, pk):
        self.get_object()
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(data={"success": serializer.data})

    def destroy(self, request, pk):
        super(ArticleChatViewset, self).destroy(request, pk=pk)

        return Response(data={"success": "chat successfully deleted"})


class PersonalMessageViewset(viewsets.ModelViewSet):
    queryset = PersonalMessage.objects.all()
    permission_classes = [MessagePermissions]
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = MessageSerializer
    http_method_names = ["get", "post", "delete", "put"]

    action_serializers = {
        "create": MessageCreateSerializer,
        "retrieve": MessageSerializer,
        "list": MessageSerializer,
        "update": MessageUpdateSerializer,
        "destroy": MessageSerializer,
    }

    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)

    def get_queryset(self):
        qs = self.queryset.filter(Q(sender=self.request.user) | Q(receiver=self.request.user)).order_by('-created_at')
        return qs

    def list(self, request):
        response = super(PersonalMessageViewset, self).list(request)

        return Response(data={"success": response.data})

    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        response = super(PersonalMessageViewset, self).retrieve(request, pk=pk)

        return Response(data={"success": response.data})

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            data={"success": "Message Successfully sent", "message": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, pk):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(data={"success": serializer.data})

    def destroy(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        super(PersonalMessageViewset, self).destroy(request, pk)

        return Response(data={"success": "Message Successfuly removed!!!"})


    
