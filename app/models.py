from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from cloudinary.models import CloudinaryField

# Create your models here.

from faker import Faker

fake = Faker()

class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, username, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    profile_picture = CloudinaryField('profile_images', null=True)
    pubmed = models.CharField(max_length=255,null=True,blank=True)
    google_scholar = models.CharField(max_length=255,null=True,blank=True)
    institute = models.CharField(max_length=255,null=True,blank=True)
    email_notify = models.BooleanField(default=True)
    email_verified = models.BooleanField(default=False)

    objects = UserManager()

    class Meta:
        db_table = 'user'

    def __int__(self) -> int:
        return self.id
    
    def profile_pic_url(self):
        return (
            f"https://res.cloudinary.com/dapuxfgic/{self.profile_picture}"
        )


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.TextField(null=False)
    
    class Meta:
        db_table = 'user_activity'
    
    def __str__(self) -> str:
        return f"{self.user}-{self.action}"
    
class EmailVerify(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.IntegerField(blank=True,null=True)
    
    class Meta:
        db_table = 'email_verify'

    def __str__(self) -> str:
        return str(self.id)
    
class ForgetPassword(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.IntegerField(blank=True,null=True)
    
    class Meta:
        db_table = 'forgot_password'

    def __str__(self) -> str:
        return str(self.id)

    
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
        constraints = [
            models.UniqueConstraint(fields=['community', 'user'], name='unique_admin_per_community'),
            models.UniqueConstraint(fields=['user', 'is_admin'], condition=models.Q(is_admin=True), name='only_one_community_admin')
        ]
        
    def __str__(self) -> str:
        return f"{self.user} - {self.community}"

class UnregisteredUser(models.Model):
    article = models.ForeignKey("app.Article", on_delete=models.CASCADE)
    fullName = models.CharField(max_length=255, null=False)
    email = models.EmailField(max_length=255, null=True,blank=True)

    class Meta:
        db_table = 'unregistered_user'

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
    article_file = CloudinaryField('articles_file')
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
    published_article_file = CloudinaryField('published_article_file',blank=True)
    published = models.CharField(max_length=255, null=True)
    published_date = models.DateTimeField(null=True,blank=True)
    Code = models.CharField(max_length=100, null=True, blank=True)
    Abstract = models.TextField(blank=True, null=True, max_length=5000)
    authors = models.ManyToManyField(User,through="Author",related_name="article_authors")
    community = models.ManyToManyField(Community, through="CommunityMeta")
    views = models.IntegerField(default=0)
    doi = models.CharField(max_length=255, null=True, blank=True)
    
    reviewer = models.ManyToManyField("app.OfficialReviewer", through='ArticleReviewer', related_name='article_reviewers')
    moderator = models.ManyToManyField("app.Moderator", through='ArticleModerator', related_name='article_moderators')
    blocked_users = models.ManyToManyField(User, through='ArticleBlockedUser')
    
    parent_article = models.ForeignKey('self', related_name='versions',null=True, blank=True ,on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'article'    

    def __str__(self) -> str:
        return self.article_name
    
    @property
    def article_file_url(self):
        if self.article_file is None:
            return (
                f"https://res.cloudinary.com/dapuxfgic/None"
            )
        return (
            f"https://res.cloudinary.com/dapuxfgic/{self.article_file}"
        )

    @property    
    def published_article_file_url(self):
        return (
            f"https://res.cloudinary.com/dapuxfgic/{self.published_article_file}"
        )

    
                
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
        unique_together = ('article', 'User')

    def __str__(self) -> str:
        return self.User.username

class CommentBase(models.Model):
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article,on_delete=models.CASCADE)
    Comment = models.TextField(max_length=20000)
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)], null=True, blank=True)
    confidence = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    Title = models.CharField(max_length=200,null=False)
    Comment_date = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', related_name='replies',on_delete=models.CASCADE, null=True, blank=True)
    tag = models.CharField(max_length=255, null=False, default='public')
    comment_type = models.CharField(max_length=255,null=False, default='publiccomment')
    types = models.options = (
        ('review', 'Review'),
        ('decision', 'Decision'),
        ('comment', 'Comment'),
    )
    Type = models.CharField(max_length=10, choices=types, default='comment')
    version = models.ForeignKey('self', related_name='versions',null=True, blank=True ,on_delete=models.CASCADE)


    class Meta:
        db_table = "comment_base"
        
class HandlersBase(models.Model):
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    handle_name = models.CharField(max_length=255, null=False, unique=True)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)

    class Meta:
        db_table = "handler_base"
        unique_together = ['User', 'handle_name', 'article']
    
    
class LikeBase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(CommentBase, on_delete=models.CASCADE, related_name="posts")
    value = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)], null=True, blank=True)

    
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
    about = models.CharField(max_length=500, null=True)
    summary = models.CharField(max_length=500, null=True)
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
    image = CloudinaryField('social_post_images', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'social_post'
        
    def __str__(self):
        return self.post
    
    def image_url(self):
        return (
            f"https://res.cloudinary.com/dapuxfgic/{self.image}"
        )

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

class BookMark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE)

    class Meta:
        db_table = 'bookmark'
        unique_together = ['user','post']

def message_media(self, instance, filename):
    if filename:
        return f"message_media/{instance.id}/{filename}"

class PersonalMessage(models.Model):
    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    channel = models.CharField(max_length=255)
    receiver = models.ForeignKey(User, related_name="received_messages",null=True,blank=True, on_delete=models.CASCADE)
    body = models.TextField(null=True)
    media = CloudinaryField(message_media, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "personal_message"

    def __str__(self) -> str:
        return self.body


class ArticleMessage(models.Model):
    sender = models.ForeignKey(User, related_name="sent_article_messages", on_delete=models.CASCADE)
    channel = models.CharField(max_length=255)
    article = models.ForeignKey(Article,related_name="article_group", on_delete=models.CASCADE)
    media = CloudinaryField(message_media, null=True)
    body = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "article_message"

    def __str__(self) -> str:
        return self.body