from typing import Iterable, Optional
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.

from faker import Faker

fake = Faker()


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.TextField(null=False)
    
    class Meta:
        db_table = 'user_activity'
    
    def __str__(self) -> str:
        return f"{self.user}-{self.action}"
    
class ForgetPassword(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.IntegerField(blank=True,null=True)
    
    class Meta:
        db_table = 'forgot_password'

    def __str__(self) -> str:
        return str(self.id)

class UserMeta(models.Model):
    pubmed = models.CharField(max_length=255,null=True,blank=True)
    google_scholar = models.CharField(max_length=255,null=True,blank=True)
    institute = models.CharField(max_length=255,null=True,blank=True)
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    email_notify = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_meta'
    
class Community(models.Model):
    title = models.CharField(max_length=300, unique=True, name='Community_name')
    subtitle = models.CharField(max_length=300, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateField(auto_now_add=True, null=True)
    github = models.URLField(max_length=200, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    website = models.CharField(max_length=300, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    members = models.ManyToManyField(User, through="CommunityMember", related_name='members')
    
    class Meta:
        db_table = 'community'

    def __str__(self):
        return self.Community_name
    
class CommunityMember(models.Model):
    community = models.ForeignKey("app.Community", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_reviewer = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'community_member'
        
    def __str__(self) -> str:
        return f"{self.user} - {self.community}"

class OfficialReviewer(models.Model):
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    Official_Reviewer_name = models.CharField(max_length=100)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, null=True, blank=True)
    
    
    class Meta:
        db_table = 'officialreviewer'
        unique_together = ['User', 'community']

    def __str__(self) -> str:
        return self.User.username

class Article(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    article_name = models.CharField(max_length=300, unique=True)
    article_file = models.FileField(upload_to='articles/')
    Public_date = models.DateTimeField(auto_now_add=True, null=True)
    visibility = models.options = (
        ('public', 'Public'),
        ('private', 'Private'),
    )
    keywords = models.CharField(max_length=255,null=False)
    authorstring = models.CharField(max_length=255,null=False)
    status = models.CharField(max_length=10, choices=visibility, default='public')
    video = models.CharField(max_length=255, blank=True, null=True)
    link = models.CharField(max_length=255, blank=True, null=True)
    license = models.CharField(max_length=255,null=True)
    published_article_file = models.FileField(upload_to='published/',blank=True)
    published = models.CharField(max_length=255, null=True)
    Code = models.CharField(max_length=100, null=True, blank=True)
    Abstract = models.TextField(null=True, max_length=5000)
    authors = models.ManyToManyField(User,through="Author",related_name="article_authors")
    community = models.ManyToManyField(Community, through="CommunityMeta")
    views = models.IntegerField(default=0)
    
    reviewer = models.ManyToManyField("app.OfficialReviewer", through='ArticleReviewer', related_name='article_reviewers')
    moderator = models.ManyToManyField("app.Moderator", through='ArticleModerator', related_name='article_moderators')
    blocked_users = models.ManyToManyField(User, through='ArticleBlockedUser')
    
    parent_article = models.ForeignKey('self', related_name='versions',null=True ,on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'article'    

    def __str__(self) -> str:
        return self.article_name
    
    # def save(self, *args, **kwargs):
    #     self.id = uuid.uuid4().hex
    #     super(Article, self).save()

class ArticleRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0, validators=[MinValueValidator(0),MaxValueValidator(5)])

    class Meta:
        db_table = 'article_rating'
        unique_together = ['user', 'article']
    
                
class ArticleReviewer(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    officialreviewer = models.ForeignKey('app.OfficialReviewer', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'article_reviewer'
        
    def __str__(self) -> str:
        return self.article.article_name

class ArticleBlockedUser(models.Model):
    article = models.ForeignKey(Article,on_delete=models.CASCADE,related_name='Article')
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    class Meta:
        db_table = 'article_blocked_user'
    
class ArticleModerator(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    moderator = models.ForeignKey('app.Moderator', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'article_moderator'
        
    def __str__(self) -> str:
        return self.article.article_name

class Author(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'author'

    def __str__(self) -> str:
        return self.User.username

class CommentBase(models.Model):
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article,on_delete=models.CASCADE)
    Comment = models.TextField(max_length=5000)
    Title = models.CharField(max_length=200,null=False)
    summary = models.TextField(max_length=5000,null=True)
    strength_weakness = models.TextField(max_length=5000,null=True)
    border_impacts = models.TextField(max_length=5000,null=True)
    Comment_date = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', related_name='replies',on_delete=models.CASCADE, null=True, blank=True)
    tag = models.CharField(max_length=255, null=False, default='public')
    comment_type = models.CharField(max_length=255,null=False, default='publiccomment')
    recommendations = models.TextField(max_length=5000,null=True)
    types = models.options = (
        ('review', 'Review'),
        ('decision', 'Decision'),
        ('comment', 'Comment')
    )
    Type = models.CharField(max_length=10, choices=types, default='comment')


    class Meta:
        db_table = "comment_base"
        
class HandlersBase(models.Model):
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    handle_name = models.CharField(max_length=255, null=False, unique=True)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)

    class Meta:
        db_table = "handler_base"
        unique_together = ['User', 'handle_name', 'article']

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=False)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'message'

    def __str__(self):
        return self.body
    
    
class LikeBase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(CommentBase, on_delete=models.CASCADE, related_name="posts")
    value = models.CharField(max_length=10, choices=(('Like', 'Like'), ('Unlike', 'Unlike')))
    
    class Meta:
        db_table = 'like_base'

class Rank(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rank = models.IntegerField(default=0)
    
    class Meta:
        db_table ='rank'

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table ='notification'

    def __str__(self):
        return self.message

class Subscribe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)

    class Meta:
        db_table ='subscribe'

    def __str__(self):
        return self.user.username
    
class Favourite(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'favourite'
        unique_together = ['user','article']
    def __str__(self) -> str:
        return self.article.article_name
    
class Moderator(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table= 'moderator'
        unique_together = ["user", "community"]
        
    def __str__(self) -> str:
        return self.user.username
    
class CommunityMeta(models.Model):  
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="article_meta")
    ARTICLE_STATUS = {
        ('submitted', 'submitted'),
        ('in review', 'in review'),
        ('accepted', 'accepted'),
        ('rejected', 'rejected')
    }
    status = models.CharField(max_length=255, choices=ARTICLE_STATUS)
    
    class Meta:
        db_table = 'community_meta'
        unique_together = ["article", "community"]
        
    def __str__(self) -> str:
        return f"{self.community} - {self.article}"


class CommunityRequests(models.Model):
    about = models.CharField(max_length=255, null=True)
    summary = models.CharField(max_length=255, null=True)
    user = models.ForeignKey(User, related_name='requests', on_delete=models.CASCADE)
    community = models.ForeignKey(Community, related_name='requests', on_delete=models.CASCADE)
    REQUEST_STATUS = {
        ('pending','pending'),
        ('approved','approved'),
        ('rejected','rejected')
    }
    status = models.CharField(max_length=10, null=False, choices=REQUEST_STATUS)

    class Meta:
        db_table = 'community_request'

    def __str__(self):
        return f"{self.community.Community_name}-{self.user.username}"
    

class SocialPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_post'
        
    def __str__(self):
        return self.post

class SocialPostComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        db_table = 'social_comment'
        
    def __str__(self):
        return self.comment

class SocialPostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name='likes')
    
    class Meta:
        db_table = 'social_like'
        
    def __str__(self):
        return self.value

class SocialPostCommentLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(SocialPostComment, on_delete=models.CASCADE, related_name='likes')
    
    class Meta:
        db_table = 'social_comment_like'
        
    def __str__(self):
        return self.value

class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    
    class Meta:
        db_table = 'follow'
        
    def __str__(self):
        return self.followed_user
    
class PersonalMessage(models.Model):
    sender = models.ForeignKey(User, related_name='sender', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'personal_message'
        
    def __str__(self):
        return self.body