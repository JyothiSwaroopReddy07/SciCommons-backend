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
from django.db.models import Q
# from app.filters import ArticleFilter, ReviewFilter, DecisionFilter
from app.models import *
from app.serializer import *
from app.permissions import *

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
        'update':UserUpdateSerializer,
        'forgot_password':ForgotPasswordSerializer,
        'reset_password':ResetPasswordSerializer,
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
        queryset = Author.objects.filter(User_id=request.user.id)
        serializer = AuthorSerializer(data=queryset, many=True)
        serializer.is_valid()
        articles = serializer.data
        return Response(data={"success": articles})
    
    @action(methods=['get'], detail=False, url_path="(?P<username>.+)/articles", permission_classes=[permissions.IsAuthenticated])
    def getUserArticles(self, request, username):
        queryset = User.objects.filter(username=username)
        serializer = UserSerializer(data=queryset, many=True)
        serializer.is_valid()
        user = serializer.data
        queryset = Author.objects.filter(User_id=user[0]["id"])
        serializer = AuthorSerializer(data=queryset, many=True)
        serializer.is_valid()
        articles = serializer.data
        return Response(data={"success": articles})

    @action(methods=['get'], detail=False,permission_classes=[permissions.IsAuthenticated,])
    def get_current_user(self, request, pk=None):
        """
        get logged in user
        """
        serializer = self.get_serializer(self.get_authenticated_user())
        # prepare response
        return Response(data={"success": serializer.data})

    @action(methods=['post'], detail=False,permission_classes=[permissions.AllowAny,])
    def forgot_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # generate a otp for user
        otp = random.randint(100000, 999999)


        try:
            user = User.objects.get(email=serializer.data['email'])
            forget = ForgetPassword(user=user, otp=otp)
            forget.save()

            email_from = settings.EMAIL_HOST_USER
            email_subject = "Reset Password"
            email_body = "You have forgot you account password. Your OTP is " + str(otp)
            send_mail(email_subject, email_body, email_from, [serializer.data['email']], fail_silently=False)
            # return redirect('resetPassword')
            return Response(data={"success": "code sent to your email"})
        except Exception as e:
            messages.error(request, 'An error accured. Please try again.')
            # return render(request, 'forgetPassword.html')
        
    @action(methods=['post'],url_path="reset_password", detail=False,permission_classes=[permissions.AllowAny,])
    def reset_password(self, request):
        otp = request.data.get('otp')
        password = request.data.get('password')
        password2 = request.data.get('password2')

        try:
            forget = ForgetPassword.objects.get(otp=otp)
            user = forget.user
            if password == password2:
                user.set_password(password)
                user.save()
                forget.delete()
                return Response(data={"success": "password reset successfully"})
            else:
                messages.error(request, 'Password not matching.')
                return Response(data={"error": "Password not matching"})
                # return redirect('resetPassword')
        except Exception as e:
            messages.error(request, 'Invalid OTP.')
            return Response(data={"error":"Invalid OTP."})
            # return redirect('resetPassword')


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
        "get_requests":CommunityRequestSerializer,
        "approve_request":ApproverequestSerializer
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
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(data={"success": "member promoted successfully"})
    
    @action(methods=['DELETE'],detail=False, url_path='(?P<Community_name>.+)/remove_member/(?P<user_id>.+)',permission_classes=[CommunityPermission]) 
    def remove_member(self, request, Community_name, user_id):
        
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        
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

        return Response(data={"success":serializer.data})

class SubscribeViewset(viewsets.ModelViewSet):
    queryset = Subscribe.objects.all()
    permission_classes = [SubscribePermission]
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = SubscribeSerializer
    http_method_names = ['post', 'delete']
    
    action_serializers = {
        "create": SubscribeSerializer,
        "destroy": SubscribeSerializer
    }

    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)

    def get_queryset(self):
        qs = self.queryset.filter(User=self.request.user)
        return qs
    
    def create(self, request):
        
        response = super(SubscribeViewset, self).create(request)
        created_object_id = response.data["id"]
        
        return Response(data={"success": "subscribed successfully","id": created_object_id })
    
    def destroy(self, request, pk ):

        super(SubscribeViewset, self).destroy(request,pk=pk)

        return Response(data={"success": "Unsubscribed successfully"})


    
class ArticleViewset(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    permission_classes = [ArticlePermission]
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    http_method_names = ['post', 'get', 'put', 'delete']
    
    # filterset_class = ArticleFilter
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
        "updateViews": ArticleViewsSerializer
        # "block_user": ArticleBlockUserSerializer
    }
    
    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)
    
    def get_queryset(self):
        community = self.request.query_params.get("community_name", None)
        
        if community is not None:
            communities = CommunityMeta.objects.filter(community__Community_name=community)
            qs = self.queryset.filter(id__in=[community.article.id for community in communities])
            return qs
        else:
            qs = self.queryset
            return qs
    
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
        print(request.data)
        response = super(ArticleViewset, self).create(request)
    
        return Response(data={"success": "Article successfully submitted"})


    def update(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(data={"success": "Article successfully updated"})


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
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        serializer = self.get_serializer(obj ,data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(data={"success":"article approved"})
    
    @action(methods=['post'],detail=False, url_path='(?P<pk>.+)/reject_article', permission_classes=[ArticlePermission])    
    def reject_article(self, request, pk):
        '''
        admin approve article and select reviewers and moderators
        '''
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
    
    # @action(methods=['post'],detail=False, url_path='(?P<pk>.+)/block_user', permission_classes=[ArticlePermission])
    # def block_user(self, request, pk):
    #     obj = self.get_object()

    #     serialzer = self.get_serializer(obj, data=request.data, partial=True)
    #     serialzer.is_valid(raise_execption=True)
    #     serialzer.save()
    #     return Response(data={"success":f"user blocked successfully"})
      
class CommentViewset(viewsets.ModelViewSet):
    queryset = CommentBase.objects.all()
    queryset2 = LikeBase.objects.all()
    permission_classes = [CommentPermission]    
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = CommentSerializer
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
        if article is not None:
            if Type is not None:
                if tag is not None:
                    if comment_type is not None:
                        qs = self.queryset.filter(article=article,tag=tag,Type=Type,comment_type=comment_type)
                    else:
                        qs = self.queryset.filter(article=article,tag=tag,Type=Type)
                else:
                    if comment_type is not None:
                        qs = self.queryset.filter(article=article,Type=Type,comment_type=comment_type)
                    else:
                        qs = self.queryset.filter(article=article,Type=Type)
            else:
                if tag is not None:
                    if comment_type is not None:
                        qs = self.queryset.filter(article=article,tag=tag,Type__in=['review', 'decision'],comment_type=comment_type)
                    else:
                        qs = self.queryset.filter(article=article,tag=tag,Type__in=['review', 'decision'])
                else:
                    if comment_type is not None:
                        qs = self.queryset.filter(article=article,Type__in=['review', 'decision'],comment_type=comment_type)
                    else:
                        qs = self.queryset.filter(article_id=article,Type__in=['review', 'decision'])
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
        if request.data["parent_comment"]:
            request.data["Type"] = "comment"

        if request.data["Type"] == 'decision':
            moderators_arr = [moderator for moderator in ArticleModerator.objects.filter(article=request.data["article"],moderator__user = request.user)]
            if len(moderators_arr)>0:
                if self.queryset.filter(article=request.data["article"],User=request.user,Type="decision").first():
                    return Response(data={"error": "You have already made decision!!!"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    super(CommentViewset, self).create(request)
                    return Response(data={"success":"Decision successfully added"})
            
            else: 
                return Response(data={"error": "You can't write a decision on the article!!!"}, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.data['Type'] == 'review':
            c = ArticleModerator.objects.filter(article=request.data["article"],moderator__user = request.user).count()
            if c > 0:
                return Response(data={"error": "You can't make a review over article"}, status=status.HTTP_400_BAD_REQUEST)
            
            count = CommentBase.objects.filter(article=request.data["article"],User=request.user,tag=request.data['tag'],Type='review').count()
            if count == 0:
                super(CommentViewset, self).create(request)

                return Response(data={"success":"Review successfully added"})
            
            else: 
                return Response(data={"error":"Review already added by you!!!"}, status=status.HTTP_400_BAD_REQUEST)
                
        else:
            if request.data['Type'] == 'comment' and request.data['parent_comment'] is None:
                return Response(data={"error":"Comment must have a parent instance"}, status=status.HTTP_400_BAD_REQUEST)
            
            super(CommentViewset, self).create(request)

            return Response(data={"success":"Comment successfully added"})


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
        
        if serializer.data['value'] == 'Like':
            comment = self.queryset.get(id=serializer.data['post'])
            handler = HandlersBase.objects.filter(User=request.user, article=comment.article).first()
            if not handler: 
                handler = HandlersBase.objects.create(User=request.user, article=comment.article, handle_name=fake.name())
                handler.save()
            # check if user already liked the comment
            if LikeBase.objects.filter(user=self.request.user, post=comment, value='Like').first():
                return Response({'error': 'comment already liked.'})
            
            else:
                # check if user already disliked the comment
                handle = HandlersBase.objects.filter(User=self.request.user,article=comment.article).first()
                unlike = LikeBase.objects.filter(user=self.request.user, post=comment, value='Unlike').first()
                if unlike:
                    unlike.delete()

                like = LikeBase.objects.create(user=self.request.user, post=comment, value='Like')
                like.save()
                
                rank = Rank.objects.filter(user=self.request.user).first()
                if rank:
                    rank.rank += 1
                    rank.save()

                else:
                    rank = Rank.objects.create(user=self.request.user, rank=1)
                    rank.save()

                notification = Notification.objects.create(user=comment.User, message=f'{handle.handle_name} liked your comment on {comment.article.article_name}', link=f'/venues/{comment.article.community}/{comment.article.community}')
                notification.save()
                
                send_mail('Someone liked your comment', f'{handle.handle_name} liked your comment on {comment.article.article_name}', settings.EMAIL_HOST_USER, [comment.User.email], fail_silently=True)
            
                return Response({'success': 'Comment liked successfully.'})
            
        elif serializer.data['value'] == 'Unlike':
            comment = self.queryset.get(id=serializer.data['post'])
            handler = HandlersBase.objects.filter(User=request.user, article=comment.article).first()
        
            if not handler: 
                handler = HandlersBase.objects.create(User=request.user, article=comment.article, handle_name=fake.name())
                handler.save()
            # check if user already liked the comment
            if LikeBase.objects.filter(user=self.request.user, post=comment, value='Unlike').first():
                return Response({'error': 'Comment already unliked.'})
            else:
                # check if user already liked the comment
                handle = HandlersBase.objects.filter(User=self.request.user,article=comment.article).first()
                like = LikeBase.objects.filter(user=self.request.user, post=comment, value='Like').first()
                if like:
                    like.delete()

                unlike = LikeBase.objects.create(user=self.request.user, post=comment, value='Unlike')
                unlike.save()

                rank = Rank.objects.filter(user=self.request.user).first()
                if rank:
                    rank.rank -= 1
                    rank.save()
                    
                else:
                    rank = Rank.objects.create(user=self.request.user)
                    rank.rank -= 1
                    rank.save()
                
                notification = Notification.objects.create(user=comment.User, message=f'{handle.handle_name} disliked your comment on {comment.article.article_name}', link=f'/venues/{comment.article.community}/{comment.article.community}')
                notification.save()
                         
                send_mail('Someone disliked your comment', f'{handle.handle_name} disliked your comment on {comment.article.article_name}', settings.EMAIL_HOST_USER, {comment.User.email}, fail_silently=True)
                                   

                return Response({'success': 'Comment disliked successfully.'})

class ChatViewset(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    permission_classes = [GeneralPermission]    
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = ChatSerializer
    http_method_names = ['post', 'get', 'put', 'delete']
    
    action_serializer = {
        "create":ChatCreateSerializer
    }
    
    def get_serializer_class(self):
        return self.action_serializer.get(self.action, self.serializer_class)
    
    def get_queryset(self):
        article = self.request.query_params.get("article", None)
        if article is not None:
            qs = self.queryset.filter(article=article).order_by('created_at')
        else:
            qs = []
            
        return qs
    
    def list(self, request):
        response = super(ChatViewset , self).list(request)
    
        return Response(data={"success":response.data})
    
    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(ChatViewset, self).retrieve(request,pk=pk)
    
        return Response(data={"success":response.data})
    
    def create(self, request):
        
        response = super(ChatViewset, self).create(request)
        
        message_data = response.data
        message_data['sender'] = request.user.username
        
        article = Article.objects.filter(id=message_data["article"]).first()
        
        channel_layer = get_channel_layer()
        
        channel_name = article.article_name
        group_name = f"chat_{channel_name.split('_')[0]}"
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'chat_message',
                'message': message_data['body']
            }
        )
        return Response(data={"success":response.data})
    
    def update(self, request, pk):

        obj = self.get_object()
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(data={"success":serializer.data})


    def destroy(self, request, pk ):

        super(CommentViewset, self).destroy(request,pk=pk)

        return Response(data={"success":"chat successfully deleted"})

    

class NotificationViewset(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    permission_classes = [NotificationPermission]    
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = NotificationSerializer
    http_method_names = ['get', 'delete']
        
    def get_queryset(self):
        qs = self.queryset.filter(user=self.request.user)
        return qs
    
    def list(self, request):
        response = super(NotificationViewset , self).list(request)
    
        return Response(data={"success":response.data})
    
    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(NotificationViewset, self).retrieve(request,pk=pk)
    
        return Response(data={"success":response.data})
    
    def destroy(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(NotificationViewset, self).destroy(request, pk)
    
        return Response(data={"success":"Notification deleted successfully."})
    
    
class FavouriteViewset(viewsets.ModelViewSet):
    queryset = Favourite.objects.all()
    permission_classes = [FavouritePermission]    
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = FavouriteSerializer
    http_method_names = ['get', 'post', 'delete']
    
    action_serializers = {
        "create":FavouriteCreateSerializer,
        "destroy":FavouriteSerializer,
        "list":FavouriteSerializer,
        "retrieve":FavouriteSerializer
    }
        
    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)
    
    def get_queryset(self):
        qs = self.queryset.filter(user=self.request.user)
        return qs
    
    def list(self, request):
        response = super(FavouriteViewset , self).list(request)
    
        return Response(data={"success":response.data})
    
    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(FavouriteViewset, self).retrieve(request,pk=pk)
    
        return Response(data={"success":response.data})
    
    def create(self, request):
        if self.queryset.filter(user=request.user,article=request.data["article"]).first() is not None:
            return  Response(data={"error":"added Already to Favourites"}, status=status.HTTP_400_BAD_REQUEST)
        response = super(FavouriteViewset, self).create(request)
        return  Response(data={"success":"added to Favourites", "id":response.data["id"]})
    
    def destroy(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(FavouriteViewset, self).destroy(request, pk)
    
        return Response(data={"success":"Removed to Favourite"})

class ArticleRatingViewset(viewsets.ModelViewSet):
    queryset = ArticleRating.objects.all()
    permission_classes = [ArticleRatingPermission]    
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = ArticleRatingSerializer
    http_method_names = ['get', 'post', 'delete', 'put']
    
    action_serializers = {
        "create": RatingCreateSerializer,
        "destroy": ArticleRatingSerializer,
        "retrieve": ArticleRatingSerializer,
        "list": ArticleRatingSerializer,
        "update": ArticleRatingSerializer
    }
        
    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)
    
    def get_queryset(self):
        qs = self.queryset.filter(user=self.request.user)
        return qs
    
    def list(self, request):
        response = super(ArticleRatingViewset , self).list(request)
        
    
        return Response(data={"success":response.data})
    
    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(ArticleRatingViewset, self).retrieve(request,pk=pk)
    
        return Response(data={"success":response.data})
    
    
    def create(self, request):
        if self.queryset.filter(article_id=request.data["article"],user=request.user).first() is not None:
            return Response(data={"error":"Rating Already added!!!"})
        response = super(ArticleRatingViewset, self).create(request)
    
        return Response(data={"success":"Rating Successfully added!!!", "id": response.data["id"]})
    
    def update(self, request, pk):

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(data={"success":serializer.data})
    
    def destroy(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(ArticleRatingViewset, self).destroy(request, pk)
    
        return Response(data={"success":"Rating Successfuly removed!!!"})
    
    @action(methods=['get'], detail=False, url_path='article/(?P<pk>.+)',permission_classes=[ArticleRatingPermission])
    def getArticleRatings(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        response = self.queryset.filter(article_id=pk, user=request.user).first()
        serializer = ArticleRatingSerializer(data=response)
        serializer.is_valid()
        return Response(data={"success": serializer.data})
    

class SocialPostViewset(viewsets.ModelViewSet):
    queryset = SocialPost.objects.all()
    permission_classes = [SocialPostPermission]    
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = SocialPostSerializer
    http_method_names = ['get', 'post', 'delete', 'put']
    
    action_serializers = {
        "create": SocialPostSerializer,
        "destroy": SocialPostSerializer,
        "retrieve": SocialPostGetSerializer,
        "list": SocialPostListSerializer,
        "update": SocialPostSerializer,
        "like": SocialPostLikeSerializer
    }
        
    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)
    
    def get_queryset(self):
        qs = self.queryset
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

    @action(methods=['post'], detail=False, permission_classes=[SocialPostPermission])
    def like(self, request):
        post = SocialPost.objects.get(id=request.data["post"])
        if SocialPostLike.objects.filter(post=post, user=request.user).first() is not None:
            return Response(data={"error":"Already Liked!!!"})
        SocialPostLike.objects.create(post=post, user=request.user)
        return Response(data={"success":"Liked!!!"})



class SocialPostCommentViewset(viewsets.ModelViewSet):
    queryset = SocialPostComment.objects.all()
    permission_classes = [SocialPostCommentPermission]    
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = SocialPostCommentSerializer
    http_method_names = ['get', 'post', 'delete', 'put']
    
    action_serializers = {
        "create": SocialPostCommentSerializer,
        "destroy": SocialPostCommentSerializer,
        "retrieve": SocialPostCommentGetSerializer,
        "list": SocialPostCommentListSerializer,
        "update": SocialPostCommentSerializer,
        "like": SocialPostCommentLikeSerializer
    }
        
    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)
    
    def get_queryset(self):
        qs = self.queryset.filter(user=self.request.user)
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
    
        return Response(data={"success":"Comment Successfully added!!!"})
    
    def update(self, request, pk):

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(data={"success":serializer.data})
    
    def destroy(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(SocialPostCommentViewset, self).destroy(request, pk)
    
        return Response(data={"success":"Comment Successfuly removed!!!"})

    @action(methods=['post'], detail=False, permission_classes=[SocialPostCommentPermission])
    def like(self, request):
        comment = SocialPostComment.objects.get(id=request.data["comment"])
        if SocialPostCommentLike.objects.filter(comment=comment, user=request.user).first() is not None:
            return Response(data={"error":"Already Liked!!!"})
        SocialPostCommentLike.objects.create(comment=comment, user=request.user)
        return Response(data={"success":"Liked!!!"})
    
class FollowViewset(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    permission_classes = [FollowPermission]    
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = FollowSerializer
    http_method_names = ['get', 'post', 'delete']
    
    action_serializers = {
        "create": FollowSerializer,
        "destroy": FollowSerializer,
        "retrieve": FollowSerializer,
        "list": FollowSerializer
    }
        
    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)
    
    def get_queryset(self):
        qs = self.queryset.filter(Q(sender=self.request.user) | Q(followed_user=self.request.user))
        return qs
    
    def list(self, request):
        response = super(FollowViewset , self).list(request)
    
        return Response(data={"success":response.data})
    
    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(FollowViewset, self).retrieve(request,pk=pk)
    
        return Response(data={"success":response.data})
    
    
    def create(self, request):
        response = super(FollowViewset, self).create(request)
    
        return Response(data={"success":"Following the user!!!"})
    
    def destroy(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(FollowViewset, self).destroy(request, pk)
    
        return Response(data={"success":"Unfollowed!!!"})
        

class PersonalMessageViewset(viewsets.ModelViewSet):
    queryset = PersonalMessage.objects.all()
    permission_classes = [GeneralPermission]    
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]
    serializer_class = PersonalMessageSerializer
    http_method_names = ['get', 'post', 'delete', 'put']
    
    action_serializers = {
        "create": PersonalMessageSerializer,
        "destroy": PersonalMessageSerializer,
        "retrieve": PersonalMessageSerializer,
        "list": PersonalMessageSerializer,
        "update": PersonalMessageSerializer
    }
        
    def get_serializer_class(self):
        return self.action_serializers.get(self.action, self.serializer_class)
    
    def get_queryset(self):
        qs = self.queryset.filter(Q(sender=self.request.user) | Q(receiver=self.request.user))
        return qs
    
    def list(self, request):
        response = super(PersonalMessageViewset , self).list(request)
    
        return Response(data={"success":response.data})
    
    def retrieve(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(PersonalMessageViewset, self).retrieve(request,pk=pk)
    
        return Response(data={"success":response.data})
    
    
    def create(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Get the sender and receiver users
        sender = self.request.user
        receiver = serializer.validated_data['receiver']

        # Send the message through the WebSocket
        channel_layer = get_channel_layer()
        room_name = f'personal_message_{sender.username}_{receiver.username}'
        async_to_sync(channel_layer.group_send)(
            room_name,
            {
                'type': 'new_message',
                'message': str(serializer.instance),
                'sender': sender.username
            }
        )

        return Response(data={"success":"Message Successfully sent", "message":serializer.data}, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk):

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(data={"success":serializer.data})
    
    def destroy(self, request, pk):
        obj = self.get_object()
        self.check_object_permissions(request,obj)
        response = super(PersonalMessageViewset, self).destroy(request, pk)
    
        return Response(data= { "success":"Message Successfuly removed!!!"})

