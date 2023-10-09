import django_filters
from app.models import *
from django.db.models import Count, Q, Subquery, Sum, OuterRef, Avg, Value
import django_filters 
from django.db.models import F
from django.db.models.functions import Coalesce

class ArticleFilter(django_filters.FilterSet):
    order = django_filters.MultipleChoiceFilter(
        choices=[
            ('most_viewed', 'Most Viewed'),
            ('least_viewed', 'Least Viewed'),
            ('most_recent', 'Most Recent'),
            ('least_recent', 'Least Recent'),
            ('most_favourite', 'Most Favourite'),
            ('least_favourite', 'Least Favourite'),
            ('most_rated','Most Rated'),
            ('least_rated','Least Rated'),

        ],
        method='filter_by_ordering'
    )

    class Meta:
        model = Article
        fields = []

    def filter_by_ordering(self, queryset, name, value):

        if 'most_rated' in value:
            queryset = (queryset.annotate(avg_rating=Coalesce(Avg('commentbase__rating', filter=Q(commentbase__Type='review')), Value(0.0))).order_by('-avg_rating'))
        if 'least_rated' in value:
            queryset = (queryset.annotate(avg_rating=Coalesce(Avg('commentbase__rating', filter=Q(commentbase__Type='review')), Value(0.0))).order_by('avg_rating'))
        if 'most_viewed' in value:
            queryset = queryset.order_by('-views')
        if 'least_viewed' in value:
            queryset = queryset.order_by('views')
        if 'most_recent' in value:
            queryset = queryset.order_by('-Public_date')
        if 'least_recent' in value:
            queryset = queryset.order_by('Public_date')
        if 'most_favourite' in value:
            queryset = queryset.order_by('favourite')
        if 'least_favourite' in value:
            queryset = queryset.order_by('-favourite')
    
        return queryset
    
class CommentFilter(django_filters.FilterSet):
    order = django_filters.MultipleChoiceFilter(
        choices=[
            ('most_recent', 'Most Recent'),
            ('least_recent', 'Least Recent'),
            ('most_rated','Most Rated'),
            ('least_rated','Least Rated'),
            ('most_reputed', "Most Reputed"),
            ('least_reputed', "Least Reputed")
        ],
        method='filter_by_ordering'
    )
    Type=django_filters.CharFilter(field_name='Type')
    comment_type=django_filters.CharFilter(field_name='comment_type')
    tag=django_filters.CharFilter(field_name='tag')
    article=django_filters.CharFilter(field_name='article')
    parent=django_filters.NumberFilter(field_name='parent_comment')
    version=django_filters.NumberFilter(field_name='version')
    
    class Meta:
        model = CommentBase
        fields = []

    def filter_by_ordering(self, queryset, name, value):
        if 'most_recent' in value:
            queryset = queryset.order_by('-Comment_date')
        if 'least_recent' in value:
            queryset = queryset.order_by('Comment_date')
        if 'most_rated' in value:
            query = Q(comment_type='review') | Q(comment_type='decision')
            comment_counts = CommentBase.objects.filter(query)
            comment_counts = comment_counts.values('comment').annotate(review_count=Count('comment')).values('review_count')
            queryset = queryset.annotate(comment_counts=Subquery(comment_counts))
            queryset = queryset.order_by('-comment_counts')
        if 'least_rated' in value:
            query = Q(comment_type='review') | Q(comment_type='decision')
            comment_counts = CommentBase.objects.filter(query)
            comment_counts = comment_counts.values('comment').annotate(review_count=Count('comment')).values('review_count')
            queryset = queryset.annotate(comment_counts=Subquery(comment_counts))
            queryset = queryset.order_by('comment_counts')
        if 'least_reputed' in value:
            queryset = queryset.order_by("user_rank")
        if 'most_reputed' in value:
            queryset = queryset.order_by("-user_rank")

        
        return queryset
    
class PostFilters(django_filters.FilterSet):

    order = django_filters.MultipleChoiceFilter(
        choices=[
            ('most_recent', 'Most Recent'),
            ('most_commented','Most Commented'),
            ('most_liked','Most Liked'),
            ('most_bookmarked','Most Bookmarked'),
        ],
        method='filter_by_ordering'
    )

    class Meta:
        model = SocialPost
        fields = []

    def filter_by_ordering(self, queryset, name, value):
        if 'most_recent' in value:
            if self.request.user.is_authenticated:
                queryset = queryset.order_by('-created_at').exclude(user=self.request.user)
            else:
                queryset = queryset.order_by('-created_at')
        if 'most_commented' in value:
            if self.request.user.is_authenticated:
                queryset = queryset.annotate(comment_count=Count('comments')).order_by('-comment_count').exclude(user=self.request.user)
            else:
                queryset = queryset.annotate(comment_count=Count('comments')).order_by('-comment_count')
        if 'most_liked' in value:
            if self.request.user.is_authenticated:
                queryset = queryset.annotate(like_count=Count('likes')).order_by('-like_count').exclude(user=self.request.user)
            else:
                queryset = queryset.annotate(like_count=Count('likes')).order_by('-like_count')
        if 'most_bookmarked' in value:
            if self.request.user.is_authenticated:
                queryset = queryset.annotate(bookmark_count=Count('bookmark')).order_by('-bookmark_count').exclude(user=self.request.user)
            else:
                queryset = queryset.annotate(bookmark_count=Count('bookmark')).order_by('-bookmark_count')
        return queryset