import datetime
import random
import uuid
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import IntegrityError, transaction
from faker import Faker
from django.core.mail import send_mail
from django.db.models import Avg
from django.conf import settings



fake = Faker()

from app.models import *

'''
user serializers
'''
class UserSerializer(serializers.ModelSerializer):
    rank = serializers.SerializerMethodField()
    followers = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()
    isFollowing = serializers.SerializerMethodField()
    posts = serializers.SerializerMethodField()
    profile_pic_url = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'username','profile_pic_url', 'first_name', 'last_name', 'email', 'rank', 'followers', 'following', 'isFollowing', 'posts']
        
    def get_rank(self, obj):
        rank = Rank.objects.get(user_id=obj.id)
        return f'{int(rank.rank)}'

    def get_followers(self, obj):
        followers = Follow.objects.filter(followed_user=obj.id).count()
        return followers
    
    def get_following(self, obj):
        following = Follow.objects.filter(user=obj.id).count()
        return following

    def get_isFollowing(self, obj):
        if (Follow.objects.filter(user=self.context['request'].user, followed_user=obj.id).count() > 0):
            return True 
        else:
            return False

    def get_posts(self, obj):
        posts = SocialPost.objects.filter(user=obj.id).count()
        return posts

class UserCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['username', 'profile_picture', 'first_name', 'last_name', 'email', 'password']
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = self.Meta.model.objects.filter(email=validated_data['email']).first()
        if user:
            raise serializers.ValidationError("User with mail already exists.Please use another email or Login using this mail")
        user = self.Meta.model.objects.filter(username=validated_data['username']).first()
        if user:
            raise serializers.ValidationError("Username already exists.Please use another username!!!")
        
        instance = self.Meta.model.objects.create(**validated_data)
        instance.set_password(password)
        instance.save()
        rank = Rank.objects.create(rank=0, user_id=instance.id)
        rank.save()
        send_mail("Welcome to Scicommons", "Welcome to Scicommons.We hope you will have a great time", settings.EMAIL_HOST_USER, [instance.email], fail_silently=False)

        return instance
    
class UserUpdateSerializer(serializers.ModelSerializer):
    profile_pic_url = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'profile_picture','profile_pic_url']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop("profile_picture")

        return representation
        
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, write_only=True)
    password = serializers.CharField(max_length=128, write_only=True)
    access = serializers.CharField(max_length=255, read_only=True)
    refresh = serializers.CharField(max_length=255, read_only=True)
    email = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email','id']


    def validate(self, data):
        username = data.get("username", None)
        password = data.get("password", None)
        member = User.objects.filter(username=username).first()
        if member is None:
            raise serializers.ValidationError(
                "Account does not exist. \nPlease try registering to scicommons first."
            )
        user = authenticate(username=username, password=password)

        if user and not user.is_active:
            raise serializers.ValidationError(
                "Account has been deactivated. \n Please contact your company's admin to restore your account."
            )

        if not user:
            raise serializers.ValidationError("Username or Password is wrong.")

        refresh = RefreshToken.for_user(user)
        data = {"access": str(refresh.access_token), "refresh": str(refresh)}

        UserActivity.objects.create(user=user, action=f"you Logged in at {datetime.datetime.now()}")

        return data

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    class Meta:
        fields = ["email"]
        
class ResetPasswordSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    password = serializers.CharField()
    password2 = serializers.CharField()
    
    class Meta:
        fields = ['otp', 'password', 'password2']
        

'''
community serializer
'''
class CommunitySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Community
        fields = ['id', 'Community_name', 'subtitle', 'description', 'location', 'date', 'github', 'email', 'website', 'user', 'members']

class CommunitylistSerializer(serializers.ModelSerializer):
    membercount = serializers.SerializerMethodField()
    evaluatedcount = serializers.SerializerMethodField()
    publishedcount = serializers.SerializerMethodField()
    subscribed = serializers.SerializerMethodField()
    
    class Meta:
        model = Community
        fields = ['id', 'Community_name','subtitle', 'description', 'evaluatedcount', 'subscribed',
                    'membercount','publishedcount']
    
    def get_membercount(self, obj):
        count = CommunityMember.objects.filter(community=obj.id).count()
        return count
    
    def get_evaluatedcount(self, obj):
        count = CommunityMeta.objects.filter(community=obj.id,status__in=['accepted', 'rejected', 'in review']).count()
        return count 
    
    def get_publishedcount(self, obj):
        count = CommunityMeta.objects.filter(community=obj.id, status__in=['accepted']).count()
        return count

    def get_subscribed(self, obj):
        count = Subscribe.objects.filter(community=obj.id).count()
        return count

class CommunityGetSerializer(serializers.ModelSerializer):
    isMember = serializers.SerializerMethodField()
    isReviewer = serializers.SerializerMethodField()
    isModerator = serializers.SerializerMethodField()
    isAdmin = serializers.SerializerMethodField()
    subscribed = serializers.SerializerMethodField()
    membercount = serializers.SerializerMethodField()
    publishedcount = serializers.SerializerMethodField()
    evaluatedcount = serializers.SerializerMethodField()
    isSubscribed = serializers.SerializerMethodField()
    admins = serializers.SerializerMethodField()
    
    class Meta:
        model = Community
        fields = ['id', 'Community_name','subtitle', 'description','location','date','github','email', 'evaluatedcount', 'isSubscribed', 'admins',
                    'website','user','membercount','publishedcount','isMember','isReviewer', 'isModerator', 'isAdmin','subscribed']
    

    def get_isMember(self, obj):
        count = CommunityMember.objects.filter(community=obj.id,user = self.context["request"].user).count()
        return count
    
    def get_isReviewer(self, obj):
        count = CommunityMember.objects.filter(community=obj.id,user = self.context["request"].user, is_reviewer=True).count()
        return count
    
    def get_isModerator(self, obj):
        count = CommunityMember.objects.filter(community=obj.id,user = self.context["request"].user, is_moderator=True).count()
        return count
    
    def get_isAdmin(self, obj):
        count = CommunityMember.objects.filter(community=obj.id,user = self.context["request"].user, is_admin=True).count()
        return count
    
    def get_membercount(self, obj):
        count = CommunityMember.objects.filter(community=obj.id).count()
        return count
    
    def get_evaluatedcount(self, obj):
        count = CommunityMeta.objects.filter(community=obj.id,status__in=['accepted', 'rejected', 'in review']).count()
        return count 
    
    def get_publishedcount(self, obj):
        count = CommunityMeta.objects.filter(community=obj.id, status__in=['accepted']).count()
        return count
    
    def get_isSubscribed(self, obj):
        count = Subscribe.objects.filter(user=self.context['request'].user,community=obj.id).count()
        if count > 0:
            return True
        else:
            return False
    
    def get_admins(self, obj):
        members = CommunityMember.objects.filter(community=obj.id, is_admin=True)
        admins = [member.user.username for member in members]
        return admins
        
    def get_subscribed(self, obj):
        count = Subscribe.objects.filter(community=obj.id).count()
        return count

class CommunityCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Community
        fields = ['Community_name', 'subtitle', 'description', 'location', 'date', 'github', 'email', 'website']
        
    def create(self, validated_data):
        community_name = validated_data.pop('Community_name', None)
        validated_data['Community_name'] = community_name.replace(' ','_')
        instance = self.Meta.model.objects.create(**validated_data, user=self.context['request'].user)
        instance.members.add(self.context['request'].user, through_defaults={"is_admin":True})
        instance.save()
        
        send_mail("you added new commnity", f"You have created a {instance.Community_name} community", settings.EMAIL_HOST_USER, [self.context['request'].user.email], fail_silently=False)        
        UserActivity.objects.create(user=self.context['request'].user, action=f"you have created community {instance.Community_name} ")

        return instance


class JoinRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = CommunityRequests
        fields = ['id', 'user', 'community', 'summary', 'about']
        read_only_fields = ['id', 'user']

    def create(self, validated_data):
        requests = self.Meta.model.objects.filter(status='pending', user=self.context['request'].user).first()
        if requests:
            raise serializers.ValidationError(detail={"error":"you already made request"})  
        instance = self.Meta.model.objects.create(**validated_data, status='pending', user=self.context['request'].user)
        instance.save()

        return instance

class CommunityRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = CommunityRequests
        fields = ['id', 'user', 'community', 'summary', 'about', 'status']


class CommunityRequestGetSerializer(serializers.ModelSerializer):

    username = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()
    class Meta:
        model = CommunityRequests
        fields = ['id', 'user', 'community', 'summary', 'about', 'status', 'username', 'rank']
    
    def get_username(self, obj):
        return obj.user.username
    
    def get_rank(self, obj):
        member = Rank.objects.filter(user_id=obj.user.id).first()
        return member.rank

class ApproverequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = CommunityRequests
        fields = ['id', 'user', 'community', 'summary', 'about', 'status']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
    
class CommunityUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Community
        fields = ['id','Community_name','subtitle', 'description', 'location', 'github', 'email', 'website']
        read_only_fields = ['Community_name','id']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        send_mail("you have updated community" , f'You have updated {instance.Community_name} details', settings.EMAIL_HOST_USER,[instance.user.email], fail_silently=False)
        UserActivity.objects.create(user=self.context['request'].user, action=f'you have updated deatils in {instance.Community_name}')
        return instance


class SubscribeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Subscribe
        fields = ['id', 'user', 'community']
        read_only_fields = ['id']

        

class PromoteSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only = True)
    role = serializers.CharField(write_only = True)
    
    class Meta:
        model = Community
        fields = ['user_id', 'role', 'Community_name', 'members']
        read_only_fields = ['Community_name', 'members']
        
    def update(self, instance, validated_data):
        user_id = validated_data.get('user_id', None)
        role = validated_data.get('role', None)
        
        if user_id is None:
            raise serializers.ValidationError(detail={"error": "user id can't be None"})
        print()
        member = CommunityMember.objects.filter(community=instance, user_id=user_id).first()
        
        if member is None:
            
            if role == "member":
                member = CommunityMember.objects.create(community=instance, user_id=user_id)
                member.is_reviewer = False
                member.is_moderator = False
                member.save()
                send_mail("added member" , f'You have been added as member to {instance.Community_name}', settings.EMAIL_HOST_USER , [member.user.email], fail_silently=False)
                UserActivity.objects.create(user=self.context['request'].user, action=f'you added {member.user.username} to community')
            else:
                raise serializers.ValidationError(detail={"error": "user isn't member of community"})
        
        try:
        
            if role is None:
                raise serializers.ValidationError(detail={"error": "role can't be None"})
            
            elif role == 'reviewer':
                moderator = Moderator.objects.filter(user_id=user_id, community=instance)
                if moderator.exists():
                    moderator.delete()
                OfficialReviewer.objects.create(User_id=user_id, community=instance, Official_Reviewer_name=fake.name())
                member.is_reviewer = True
                member.is_moderator = False
                member.save()
                send_mail("you are Reviewer", f'You have been added as Official Reviewer to {instance.Community_name}', settings.EMAIL_HOST_USER , [member.user.email], fail_silently=False)
                UserActivity.objects.create(user=self.context['request'].user, action=f'you added {member.user.username} to {instance.Community_name} as reviewer')
                
            elif role == 'moderator':
                reviewer = OfficialReviewer.objects.filter(User_id=user_id, community=instance)
                if reviewer.exists():
                    reviewer.delete()
                Moderator.objects.create(user_id=user_id, community=instance)
                member.is_moderator = True
                member.is_reviewer = False
                member.save()
                send_mail(" you are moderator", f'You have been added as Moderator to {instance.Community_name}', settings.EMAIL_HOST_USER , [member.user.email], fail_silently=False)
                UserActivity.objects.create(user=self.context['request'].user, action=f'you added {member.user.username} to {instance.Community_name} as moderator')
                
            elif role == 'admin':
                member.is_moderator = False
                member.is_reviewer = False
                member.is_admin = True
                member.save()
                send_mail("you are admin", f'You have been added as Admin to {instance.Community_name}', settings.EMAIL_HOST_USER , [member.user.email], fail_silently=False)
                UserActivity.objects.create(user=self.context['request'].user, action=f'you added {member.user.username} to {instance.Community_name} as admin')
                                
            elif role == 'member':
                reviewer = OfficialReviewer.objects.filter(User_id=user_id, community=instance)
                if reviewer.exists():
                    reviewer.delete()
                
                moderator = Moderator.objects.filter(user_id=user_id, community=instance)
                if moderator.exists():
                    moderator.delete()
                    
                member.is_reviewer = False
                member.is_moderator = False
                member.save()
                send_mail(f'you are added to {instance.Community_name}',f'You have been added as member to {instance.Community_name}', settings.EMAIL_HOST_USER , [member.user.email], fail_silently=False)
                UserActivity.objects.create(user=self.context['request'].user, action=f'you added {member.user.username} to {instance.Community_name}')
                    
            else:
                raise serializers.ValidationError(detail={"error": " wrong role. role can be 'reviewer','moderator','member'"}) 
            
        except IntegrityError as e:
            raise serializers.ValidationError(detail={"error": f'{member.user.username} is already {role}'}) 
        
        return instance
        
        
'''
article serializers
'''
class ArticleSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    class Meta:
        model = Article
        fields = ['id', 'article_name', 'Public_date', 'rating', 'authors']
    
    def get_rating(self, obj):
        rating = CommentBase.objects.filter(article_id=obj.id,Type='review').aggregate(Avg('rating'))['rating__avg']
        return rating


class ArticlePublishSelectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Article
        fields = ['id', 'published']

class ArticlePostPublishSerializer(serializers.ModelSerializer):

    class Meta:
        model = Article
        fields = ["id","license","published_article_file"]

class ArticlePublisherSerializer(serializers.ModelSerializer):
    published_article_file_url = serializers.ReadOnlyField()

    class Meta:
        model = Article
        fields = ["id", "license", "published_article_file", "published", "published_article_file_url"]

class ArticlelistSerializer(serializers.ModelSerializer):

    rating = serializers.SerializerMethodField()
    isFavourite = serializers.SerializerMethodField()
    favourites = serializers.SerializerMethodField()
    authors = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ['id', 'article_name', 'Public_date','views', 'authors','rating', 'isFavourite', 'keywords', 'favourites']
    
    def get_rating(self, obj):
        rating = CommentBase.objects.filter(article_id=obj.id,Type='review').aggregate(Avg('rating'))['rating__avg']
        return rating
    
    def get_favourites(self, obj):
        favourites = Favourite.objects.filter(article_id=obj.id).count()
        return favourites
    
    def get_isFavourite(self, obj):
        if (Favourite.objects.filter(article=obj.id,user=self.context['request'].user).count() > 0):
            return True 
        else:
            return False
    
    def get_authors(self, obj):
        authors = [user.username for user in obj.authors.all()]
        return authors

        

class ArticleGetSerializer(serializers.ModelSerializer):
    versions = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    isArticleReviewer = serializers.SerializerMethodField()           
    isArticleModerator = serializers.SerializerMethodField()
    isFavourite = serializers.SerializerMethodField()
    isAuthor = serializers.SerializerMethodField()
    userrating = serializers.SerializerMethodField()
    commentcount = serializers.SerializerMethodField()
    authors = serializers.SerializerMethodField()
    article_file_url = serializers.ReadOnlyField()

    class Meta:
        model = Article
        fields = ['id', 'article_name', 'article_file_url', 'Public_date', 'Code', 'Abstract','views','video',
                    'link', 'authors','rating','versions','isArticleReviewer','isArticleModerator','isAuthor',
                    'isFavourite', 'userrating','commentcount']
    
    def get_versions(self, obj):
        
        if not obj.parent_article:
            serialized_child_articles  = ArticleGetSerializer(obj.versions.all(), many=True)
            return serialized_child_articles.data
        
        else:
            child_articles = Article.objects.exclude(id=obj.id).filter(parent_article=obj.parent_article)
            serialized_child_articles  = ArticleGetSerializer(child_articles, many=True)
            return serialized_child_articles.data
    
    def get_commentcount(self, obj):
        count = CommentBase.objects.filter(article_id=obj.id).count()
        return count
    
    def get_rating(self, obj):
        rating = CommentBase.objects.filter(article_id=obj.id,Type='review').aggregate(Avg('rating'))['rating__avg']
        return rating
    
    def get_isArticleReviewer(self, obj):
        if (ArticleReviewer.objects.filter(article=obj.id,officialreviewer__User_id=self.context['request'].user).count()>0):
            return True
        else:
            return False
    
    def get_isArticleModerator(self, obj):
        if(ArticleModerator.objects.filter(article=obj.id,moderator__user_id=self.context['request'].user).count()>0):
            return True
        else:
            return False
    
    def get_isAuthor(self, obj):
        if(Author.objects.filter(article=obj.id,User=self.context['request'].user).count()>0):
            return True
        else:
            return False
    
    def get_isFavourite(self, obj):
        if (Favourite.objects.filter(article=obj.id,user=self.context['request'].user).count() > 0):
            return True 
        else:
            return False
    
    def get_userrating(self, obj):
        rating = CommentBase.objects.filter(article_id=obj.id,Type='review',User=self.context['request'].user).first()
        if rating is None:
            return "null"
        return f'{rating.rating}'
    
    def get_authors(self, obj):
        authors = [user.username for user in obj.authors.all()]
        return authors

class ArticleBlockUserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Article
        fields = ["id", "article_name", "blocked_users", 'user_id']
        read_only_fields = ["id", "article_name", "blocked_users"]

    def update(self, instance, validated_data):
        instance.blocked_users.add(validated_data["user"])
        instance.save()

        return instance
        

class ArticleViewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['views']

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id','status']

class ArticleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['article_file','Code','Abstract','authors','video', 'link']
        
       

class ArticleCreateSerializer(serializers.ModelSerializer):
    authors = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    communities = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    class Meta:
        model = Article
        fields = ['id', 'article_name','keywords', 'article_file', 'Code', 'Abstract', 'authors','video','link', 'parent_article', 'communities']
        read_only_fields = ['id']
    def create(self, validated_data):
        parent_article = validated_data.pop('parent_article', None)
        if parent_article is None:
            authors = validated_data.pop("authors", [])
            communities = validated_data.pop("communities", [])
            communities.pop(0)
            authors.pop(0)
            name = validated_data.pop('article_name')
            keywords = validated_data.pop('keywords')
            keywords.replace(' ','_')
            validated_data['article_name'] = name.replace(' ','_')
            validated_data['keywords'] = keywords
            instance = self.Meta.model.objects.create(**validated_data,id=uuid.uuid4().hex)
            Author.objects.create(User=self.context['request'].user, article=instance)
            authorstr = ""
            if len(authors)!=0:
                with transaction.atomic():
                    for author in authors:
                        author = Author.objects.create(User_id=author, article=instance)
                        authorstr += author.User.first_name + '_' + author.User.last_name + "||"
                        send_mail("Article added",f"You have added an article {instance.article_name} to SciCommons", settings.EMAIL_HOST_USER, [author.User.email], fail_silently=False)
                        UserActivity.objects.create(user=self.context['request'].user, action=f'you added article {instance.article_name}')
            instance.authorstring = authorstr
            if len(communities) > 0 and instance.link is not None:
                raise serializers.ValidationError(detail={"error": "you can not submit external article"})

            if len(communities) > 0:
                with transaction.atomic():
                    for community in communities:
                        community_meta = CommunityMeta.objects.create(community_id=community, article=instance, status='submitted')
                        community_meta.save()
                        
                        community = Community.objects.get(id=community)

                        emails = [member.user.email for member in CommunityMember.objects.filter(community=community)]
                        send_mail("New Article Alerts", f'New Article {instance.article_name} added on {community}', settings.EMAIL_HOST_USER, emails, fail_silently=False) 
            instance.save()
            return instance
        else:
            parentinstance = Article.objects.get(id=parent_article)
            authors = validated_data.pop("authors", [])
            authors.pop(0)
            name = validated_data.pop('article_name')
            keywords = validated_data.pop('keywords')
            keywords.replace(' ','_')
            validated_data['article_name'] = name.replace(' ','_')
            validated_data['keywords'] = keywords
            instance = self.Meta.model.objects.create(**validated_data,id=uuid.uuid4().hex)
            communities = [community for community in parentinstance.communities]
            instance.communities.set(communities)
            instance.parent_article = parent_article
            
            with transaction.atomic():
                for community in communities:
                    community_meta = CommunityMeta.objects.create(community_id=community, article=instance, status='submitted')
                    community_meta.save()
                    
                    community = Community.objects.get(id=community)

                    emails = [member.user.email for member in CommunityMember.objects.filter(community=community)]
                    send_mail("New Article Alerts", f'New Article {instance.article_name} added on {community}', settings.EMAIL_HOST_USER, emails, fail_silently=False) 
            instance.save()
            return instance
            
    
class SubmitArticleSerializer(serializers.Serializer):
    communities = serializers.ListField(child=serializers.CharField(), write_only=True)
    meta_id = serializers.ListField(child=serializers.CharField(), read_only=True)
    article_id = serializers.CharField()
    class Meta:
        fields = ['article_id','communities', 'meta_id']
        
    def create(self, validated_data):

        communities = validated_data.get('communities', [])
        instance = Article.objects.filter(id=validated_data['article_id']).first()
        
        if CommunityMeta.objects.filter(article=instance).first():
            raise serializers.ValidationError(detail={"error": "article already submitted"})
        
        meta_id = []
        if len(communities)==0:
            raise serializers.ValidationError(detail={"error": "communities can't be empty or None"})
        
        if instance.link is not None:
            raise serializers.ValidationError(detail={"error": "you can not submit external article"})
        
        with transaction.atomic():
            for community in communities:
                community_meta = CommunityMeta.objects.create(community_id=community, article=instance, status='submitted')
                community_meta.save()
                
                community = Community.objects.get(id=community)

                emails = [member.user.email for member in CommunityMember.objects.filter(community=community)]
                send_mail("New Article Alerts", f'New Article {instance.article_name} added on {community}', settings.EMAIL_HOST_USER, emails, fail_silently=False) 
                meta_id.append(community_meta.id)
        
        return {"meta_id":meta_id}

class InReviewSerializer(serializers.Serializer):
    status = serializers.BooleanField(read_only=True)
    community = serializers.CharField(write_only=True)
    reviwers = serializers.ListField(
        child=serializers.IntegerField(),
        read_only=True
    )
    moderator = serializers.ListField(
        child=serializers.IntegerField(),
        read_only=True
    )
    
    class Meta:
        fields = ['status', 'community', 'reviwers', 'moderator']
        
    def update(self, instance ,validated_data):
        community_meta = CommunityMeta.objects.filter(community_id=validated_data['community'], article=instance).first()
        if community_meta is None:
            raise serializers.ValidationError(detail=f'article not submitted for review {community_meta.community.Community_name}')
        community_meta.status = 'in review'
        community_meta.save()
        reviewers_arr = [reviewer for reviewer in OfficialReviewer.objects.filter(community_id = validated_data['community'])]
        moderators_arr = [moderator for moderator in Moderator.objects.filter(community_id = validated_data['community'])]

        if len(reviewers_arr)==0:
            raise serializers.ValidationError(detail={"error":"No Reviewer on Community"})

        if len(moderators_arr)==0:
            raise serializers.ValidationError(detail={"error":"No Moderator on Community"})

        if len(reviewers_arr)>=3:
            reviewers_arr = random.sample(reviewers_arr, 3)

        if len(moderators_arr)>=1:
            moderators_arr = random.sample(moderators_arr, 1)

        instance.reviewer.add(*[reviewer.id for reviewer in reviewers_arr])
        instance.moderator.add(*[moderator.id for moderator in moderators_arr])

        emails = [member.User.email for member in reviewers_arr]
        send_mail("New Article Alerts",f'You have been added as an Official Reviewer to {instance.article_name} on {community_meta.community.Community_name}', settings.EMAIL_HOST_USER, emails, fail_silently=False)

        emails = [member.user.email for member in moderators_arr]
        send_mail("New Article Alerts", f'You have been added as a Moderator to {instance.article_name} on {community_meta.community.Community_name}', settings.EMAIL_HOST_USER, emails, fail_silently=False)

        return {"status":community_meta.status, 'reviewers':instance.reviewer, 'moderator':instance.moderator}

class ApproveSerializer(serializers.Serializer):
    status = serializers.CharField()
    community = serializers.IntegerField()
    article = serializers.IntegerField(read_only=True)    
    class Meta:
        fields = ['status', 'community', 'article']

    def update(self, instance, validated_data):
        communitymeta = CommunityMeta.objects.filter(article_id=instance.id,
                                                community=validated_data['community'],
                                                article=instance).first()
        communitymeta.status = 'accepted'
        communitymeta.save()
        emails = [member.email for member in instance.authors.all()]
        send_mail(f"Article is approved", f"Your article: {instance.article_name} is approved by {communitymeta.community.Community_name}", settings.EMAIL_HOST_USER , emails, fail_silently=False)
        UserActivity.objects.create(user=self.context['request'].user, action=f'you have approved the {instance.article_name} to {communitymeta.community.Community_name}')

        return communitymeta

class RejectSerializer(serializers.Serializer):
    status = serializers.CharField()
    community = serializers.IntegerField()
    article = serializers.IntegerField(read_only=True)    
    class Meta:
        fields = ['status', 'community', 'article']

    def update(self, instance, validated_data):
        communitymeta = CommunityMeta.objects.filter(article_id=instance.id,
                                                community=validated_data['community'],
                                                article=instance).first()
        communitymeta.status = 'rejected'
        communitymeta.save()
        emails = [member.email for member in instance.authors.all()]
        send_mail(f"Article is rejected", f"Your article: {instance.article_name} is rejected by {communitymeta.community.Community_name}", settings.EMAIL_HOST_USER , emails, fail_silently=False)
        UserActivity.objects.create(user=self.context['request'].user, action=f'you have rejected the {instance.article_name} to {communitymeta.community.Community_name}')

        return communitymeta

'''
comments serializers
'''
class CommentlistSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    rank = serializers.SerializerMethodField(read_only=True)
    personal = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CommentBase
        fields = ['id', 'article', 'Comment', 'Title','Type','rating','confidence',
                        'tag','comment_type', 'user','Comment_date',
                    'parent_comment','rank','personal']
        
    def get_user(self, obj):
        handle = HandlersBase.objects.filter(User=obj.User,article=obj.article).first()
        return handle.handle_name
    
    def get_replies(self, obj):
        replies = CommentBase.objects.filter(parent_comment=obj)
        serializer = CommentSerializer(replies, many=True, context=self.context)
        return serializer.data

    def get_rank(self, obj):
        rank = Rank.objects.filter(user=obj.User).first()
        return f'{int(rank.rank)}'
    
    def get_personal(self, obj): 
        personal = (obj.User == self.context['request'].user)
        return personal

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)
    rank = serializers.SerializerMethodField(read_only=True)
    personal = serializers.SerializerMethodField(read_only=True)
    likes = serializers.SerializerMethodField(read_only=True)
    dislikes = serializers.SerializerMethodField(read_only=True)
    Liked = serializers.SerializerMethodField(read_only=True)
    Unliked = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = CommentBase
        fields = ['id', 'article', 'Comment', 'Title', 'Type', 'tag','comment_type', 'user','likes', 'dislikes','Comment_date',
                    'parent_comment','rank','personal','Liked','Unliked', 'replies', 'rating','confidence']
        
    def get_user(self, obj):
        handle = HandlersBase.objects.filter(User=obj.User,article=obj.article).first()
        return handle.handle_name
    
    def get_replies(self, obj):
        replies = CommentBase.objects.filter(parent_comment=obj)
        serializer = CommentSerializer(replies, many=True, context=self.context)
        return serializer.data

    def get_rank(self, obj):
        rank = Rank.objects.filter(user=obj.User).first()
        return f'{int(rank.rank)}'
    
    def get_personal(self, obj): 
        personal = (obj.User == self.context['request'].user)
        return personal
    
    def get_likes(self, obj):
        count = LikeBase.objects.filter(post_id=obj.id,value='Like').count()
        return count
    
    def get_dislikes(self, obj):
        count = LikeBase.objects.filter(post_id=obj.id,value='Unlike').count()
        return count
    
    def get_Liked(self, obj):
        Liked = LikeBase.objects.filter(value='Like',post_id=obj.id,user=self.context['request'].user).count()
        return Liked
    
    def get_Unliked(self, obj):
        Unliked = LikeBase.objects.filter(value='Unlike',post_id=obj.id,user=self.context['request'].user).count()
        return Unliked


class CommentCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CommentBase
        fields = ['article', 'Comment', 'Title', 'Type', 'tag','comment_type','parent_comment','rating','confidence']

    def create(self, validated_data):
        authors = [author for author in Author.objects.filter(article=validated_data["article"],User=self.context["request"].user)]
        reviewers_arr = [reviewer for reviewer in ArticleReviewer.objects.filter(article=validated_data["article"],officialreviewer__User = self.context["request"].user)]
        moderators_arr = [moderator for moderator in ArticleModerator.objects.filter(article=validated_data["article"],moderator__user = self.context["request"].user)]

        if len(authors)> 0 or len(reviewers_arr)>0 or len(moderators_arr)>0:
            validated_data["comment_type"] = "OfficialComment"
        else:
            validated_data["comment_type"] = "PublicComment"
        instance = self.Meta.model.objects.create(**validated_data,User=self.context["request"].user)
        instance.save()
        
        handler = HandlersBase.objects.filter(User=instance.User, article=instance.article).first()
        
        if not handler: 
            handler = HandlersBase.objects.create(User=instance.User, article=instance.article, handle_name=fake.name())
            handler.save()
            
        send_mail(f"you have made {instance.Type}",f"You have made a {instance.Type} on {instance.article.article_name}", settings.EMAIL_HOST_USER,[instance.User.email], fail_silently=False)
        UserActivity.objects.create(user=self.context['request'].user, action=f"You have made a {instance.Type} on {instance.article.article_name}")

        return instance    
        
class CommentUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CommentBase
        fields = ['Comment', 'Title']
        
class LikeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = LikeBase
        fields = ['post', 'value']


'''
chat serializer
'''

class ChatSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Message
        fields = ['id', 'sender', 'body', 'article', 'created_at']
    
    def get_sender(self, obj):
        user = User.objects.filter(id=obj.sender.id).first()
        return f'{user.username}'

        
class ChatCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = ['body', 'channel', 'article', 'receiver']
    
    def create(self, validated_data):
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        receiver = validated_data('receiver', None)
        sender = validated_data('sender', None)
        article = validated_data('article', None)

        instance = self.Meta.model.objects.create(**validated_data, sender=self.context['request'].user)
        instance.save()

        if receiver:
            channel = f"chat_{sender}_{receiver}"
            message = {
            "sender":instance.sender,
            "receiver":instance.receiver,
            "body":instance.body
        }
        elif article:
            channel = f"chat_{article}"
            message = {
            "article":instance.article,
            "body":instance.body
        }

        # Send the message via websockets
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            channel,
            {
                'type': 'chat_message',
                'message': message
            }
        )

        return instance

'''
notification serializer
'''
class NotificationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Notification
        fields = ["id", "user", "message", "date", "is_read", "link"]
        
'''
favourite serializer
'''
class FavouriteSerializer(serializers.ModelSerializer):
    article_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Favourite
        fields = ['id', 'article_name', 'user']
        
    def get_article_name(self, obj):
        return obj.article.article_name

class FavouriteCreateSerializer(serializers.Serializer):
    article_name = serializers.CharField(write_only=True)

    class Meta:
        model = Favourite
        fields = ['id', 'article', 'user']
        read_only_fields = ['id']
        
    def create(self, validated_data):
        
        favourite = Favourite.objects.filter(article=validated_data['article'],
                                           user=self.context['request'].user).first()
        if favourite:
            raise serializers.ValidationError({"error":"already in favourites"})
        
        instance = Favourite.objects.create(article=validated_data['article'],
                                           user=self.context['request'].user)
        instance.save()
        UserActivity.objects.create(user=self.context['request'].user, action=f"You added {instance.article.article_name} in favourite")

        return instance
               
'''
communitymeta serializers
'''
class CommunityMetaSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CommunityMeta
        fields = ['community', 'article', 'status']
        depth = 1

class CommunityMetaArticlesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMeta
        fields = ['article','status']
        depth = 1

class CommunityMetaApproveSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMeta
        fields = ['community', 'status']
        depth = 1

'''
communitymembers serializer
'''
class CommunityMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMember
        fields = ['user','is_reviewer','is_moderator','is_admin']
        depth = 1

'''
AuthorSerializer
'''
class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['article']
        depth = 1

'''
OfficialReviewerSerializer
'''
class OfficialReviewerSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficialReviewer
        fields = ['User','community']
        depth = 1

'''
ModeratorSerializer
'''
class ModeratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Moderator
        fields = ['user','community']
        depth = 1


class SocialPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialPost
        fields = ['id', 'user', 'body', 'created_at', 'image']
        read_only_fields = ['user','id','created_at', 'image']

class SocialPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialPost
        fields = ['id', 'user', 'body', 'created_at', 'image']
        read_only_fields = ['user','id','created_at', 'image']

    def create(self, validated_data):
        instance = self.Meta.model.objects.create(**validated_data, user=self.context['request'].user)
        instance.save()
        return instance

class SocialPostListSerializer(serializers.ModelSerializer):
    comments_count = serializers.SerializerMethodField(read_only=True)
    likes = serializers.SerializerMethodField(read_only=True)
    liked = serializers.SerializerMethodField(read_only=True)
    bookmarks = serializers.SerializerMethodField(read_only=True)
    isbookmarked = serializers.SerializerMethodField(read_only=True)
    username = serializers.SerializerMethodField(read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SocialPost
        fields = ['id', 'username', 'body', 'created_at', 'comments_count', 'likes', 'liked', 'bookmarks', 'isbookmarked','image', 'image_url']

    def get_username(self,obj):
        return obj.user.username
    
    def get_avatar(self,obj):
        return obj.user.profile_picture

    def get_comments_count(self, obj):
        comments_count = SocialPostComment.objects.filter(post_id=obj.id).count()
        return comments_count
    
    def get_likes(self, obj):
        likes = SocialPostLike.objects.filter(post_id=obj.id).count()
        return likes

    def get_liked(self, obj):
        liked = SocialPostLike.objects.filter(post_id=obj.id, user=self.context['request'].user).count()
        return liked

    def get_bookmarks(self,obj):
        bookmarks = BookMark.objects.filter(post_id=obj.id).count()
        return bookmarks

    def get_isbookmarked(self,obj):
        isbookmarked = BookMark.objects.filter(post_id=obj.id, user=self.context['request'].user).count()
        return isbookmarked

class SocialPostGetSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.SerializerMethodField(read_only=True)
    likes = serializers.SerializerMethodField(read_only=True)
    liked = serializers.SerializerMethodField(read_only=True)
    bookmarks = serializers.SerializerMethodField(read_only=True)
    isbookmarked = serializers.SerializerMethodField(read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)
    username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SocialPost
        fields = ['id', 'username', 'body', 'created_at', 'comments_count', 'likes', 'liked', 'comments', 'bookmarks', 'isbookmarked', 'image', 'image_url']

    def get_username(self,obj):
        return obj.user.username
    
    def get_avatar(self,obj):
        return obj.user.profile_picture
    
    def get_comments(self, obj):
        comments = SocialPostComment.objects.filter(post_id=obj.id)
        serializer = SocialPostCommentListSerializer(comments, many=True)
        return serializer.data

    def get_comments_count(self, obj):
        comments_count = SocialPostComment.objects.filter(post_id=obj.id).count()
        return comments_count
    
    def get_likes(self, obj):
        likes = SocialPostLike.objects.filter(post_id=obj.id).count()
        return likes

    def get_liked(self, obj):
        liked = SocialPostLike.objects.filter(post_id=obj.id, user=self.context['request'].user).count()
        return liked
    
    def get_bookmarks(self,obj):
        bookmarks = BookMark.objects.filter(post_id=obj.id).count()
        return bookmarks

    def get_isbookmarked(self,obj):
        isbookmarked = BookMark.objects.filter(post_id=obj.id, user=self.context['request'].user).count()
        return isbookmarked


class SocialPostCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialPostComment
        fields = ['id', 'user', 'post', 'comment', 'created_at']
        read_only_fields = ['user','id','created_at']

class SocialPostCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialPostComment
        fields = ['id', 'user', 'post', 'comment', 'created_at']
        read_only_fields = ['user','id','created_at']

    def create(self, validated_data):
        instance = self.Meta.model.objects.create(**validated_data, user=self.context['request'].user)
        instance.save()
        return instance

class SocialPostCommentListSerializer(serializers.ModelSerializer):

    likes = serializers.SerializerMethodField(read_only=True)
    liked = serializers.SerializerMethodField(read_only=True)
    replies_count = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.SerializerMethodField(read_only=True)
    username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SocialPostComment
        fields = ['id', 'username', 'post', 'comment', 'created_at', 'likes', 'liked', 'replies_count', 'avatar']
    
    def get_username(self,obj):
        return obj.user.username
    
    def get_avatar(self,obj):
        return obj.user.profile_picture

    def get_likes(self, obj):
        likes = SocialPostCommentLike.objects.filter(comment_id=obj.id).count()
        return likes
    
    def get_liked(self, obj):
        liked = SocialPostCommentLike.objects.filter(comment_id=obj.id, user=self.context['request'].user).count()
        return liked

    def get_replies_count(self, obj):
        replies_count = SocialPostComment.objects.filter(parent_comment=obj.id).count()
        return replies_count
    
class SocialPostCommentGetSerializer(serializers.ModelSerializer):
    liked = serializers.SerializerMethodField(read_only=True)
    likes = serializers.SerializerMethodField(read_only=True)
    replies_count = serializers.SerializerMethodField(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.SerializerMethodField(read_only=True)
    username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SocialPostComment
        fields = ['id', 'username', 'post', 'comment', 'created_at', 'likes', 'liked', 'replies_count', 'replies', 'avatar']

    def get_username(self,obj):
        return obj.user.username
    
    def get_avatar(self,obj):
        return obj.user.profile_picture
    
    def get_likes(self, obj):
        likes = SocialPostCommentLike.objects.filter(comment_id=obj.id).count()
        return likes
    
    def get_liked(self, obj):
        liked = SocialPostCommentLike.objects.filter(comment_id=obj.id, user=self.context['request'].user).count()
        return liked
    
    def get_replies_count(self, obj):
        replies_count = SocialPostComment.objects.filter(parent_comment=obj.id).count()
        return replies_count

    def get_replies(self, obj):
        replies = SocialPostComment.objects.filter(parent_comment=obj.id)
        serializer = SocialPostCommentListSerializer(replies, many=True)
        return serializer.data

class SocialPostLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialPostLike
        fields = ['id', 'user', 'post']
        read_only_fields = ['user','id']


class SocialPostCommentLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialPostCommentLike
        fields = ['id', 'user', 'comment']
        read_only_fields = ['user','id']


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ['id', 'user', 'followed_user']
        read_only_fields = ['user','id']

class FollowCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ['id', 'user', 'followed_user']
        read_only_fields = ['user','id']

    def create(self, validated_data):
        instance = self.Meta.model.objects.create(**validated_data, user=self.context['request'].user)
        instance.save()
        return instance

class SocialPostBookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookMark
        fields = ['id', 'user', 'post']
        read_only_fields = ['user','id']

class SocialPostBookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookMark
        fields = ['id', 'user', 'post']
        read_only_fields = ['user','id']

    def create(self, validated_data):
        instance = self.Meta.model.objects.create(**validated_data, user=self.context['request'].user)
        instance.save()
        return instance


