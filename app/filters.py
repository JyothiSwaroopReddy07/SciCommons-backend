# import django_filters
# from app.models import *
# from django.db.models import Count, Q, Subquery
# import django_filters 

# class ArticleFilter(django_filters.FilterSet):
#     order = django_filters.MultipleChoiceFilter(
#         choices=[
#             ('most_viewed', 'Most Viewed'),
#             ('least_viewed', 'Least Viewed'),
#             ('most_recent', 'Most Recent'),
#             ('oldest', 'Oldest'),
#             ('most_favourite', 'Most Favourite'),
#             ('least_favourite', 'Least Favourite'),
#             ('most_commented','Most Commented'),
#             ('least_commented','Least Commented'),

#         ],
#         method='filter_by_ordering'
#     )

#     class Meta:
#         model = Article
#         fields = []

#     def filter_by_ordering(self, queryset, name, value):
#         if 'most_viewed' in value:
#             queryset = queryset.order_by('-views')
#         if 'least_viewed' in value:
#             queryset = queryset.order_by('views')
#         if 'most_recent' in value:
#             queryset = queryset.order_by('-Public_date')
#         if 'oldest' in value:
#             queryset = queryset.order_by('Public_date')
#         if 'most_favourite' in value:
#             queryset = queryset.order_by('-favourite')
#         if 'least_favourite' in value:
#             queryset = queryset.order_by('favourite')
#         if 'most_commented' in value:
#             review_comment_counts = CommentBase.objects.filter(comment_type='review')
#             review_comment_counts = review_comment_counts.values('article').annotate(review_count=Count('article')).values('review_count')

#             queryset = queryset.annotate(review_comment_count=Subquery(review_comment_counts))

#             queryset = queryset.order_by('-review_comment_count')
#         if 'least_commented' in value:
#             review_comment_counts = CommentBase.objects.filter(comment_type='review')
#             review_comment_counts = review_comment_counts.values('article').annotate(review_count=Count('article')).values('review_count')

#             queryset = queryset.annotate(review_comment_count=Subquery(review_comment_counts))

#             queryset = queryset.order_by('review_comment_count')
#         return queryset
    
# class CommentFilter(django_filters.FilterSet):
#     order = django_filters.MultipleChoiceFilter(
#         choices=[
#             ('most_recent', 'Most Recent'),
#             ('oldest', 'Oldest'),
#             ('most_rated','Most Rated'),
#             ('by_most_reputed', "By Most Reputed")
#         ],
#         method='filter_by_ordering'
#     )
#     type=django_filters.CharFilter(field_name='comment_type')
#     visibility=django_filters.CharFilter(field_name='visibility')
#     tag=django_filters.CharFilter(field_name='tag')
#     article=django_filters.NumberFilter(field_name='article')
#     parent=django_filters.NumberFilter(field_name='parent_comment')
#     version=django_filters.NumberFilter(field_name='version')
    
#     class Meta:
#         model = CommentBase
#         fields = []

#     def filter_by_ordering(self, queryset, name, value):
#         if 'most_recent' in value:
#             queryset = queryset.order_by('-Comment_date')
#         if 'oldest' in value:
#             queryset = queryset.order_by('Comment_date')
#         if 'most_rated' in value:
#             query = Q(comment_type='review') | Q(comment_type='decision')
#             comment_counts = CommentBase.objects.filter(query)
#             comment_counts = comment_counts.values('comment').annotate(review_count=Count('comment')).values('review_count')

#             queryset = queryset.annotate(comment_counts=Subquery(comment_counts))

#             queryset = queryset.order_by('-comment_counts')
#         if 'by_most_reputed_user' in value:
#             queryset = queryset.order_by("-user_rank")

        
#         return queryset
    
# class PostFilters(django_filters.FilterSet):

#     order = django_filters.MultipleChoiceFilter(
#         choices=[
#             ('most_recent', 'Most Recent'),
#             ('oldest', 'Oldest'),
#         ],
#         method='filter_by_ordering'
#     )

#     class Meta:
#         model = SocialPost
#         fields = []

#     def filter_by_ordering(self, queryset, name, value):
#         if 'most_recent' in value:
#             queryset = queryset.order_by('-created_at')
#         if 'oldest' in value:
#             queryset = queryset.order_by('created_at')
#         if 'most_commented' in value:
#             queryset = queryset.annotate(comment_count=Count('comments')).order_by('-comment_count')
#         if 'most_liked' in value:
#             queryset = queryset.annotate(like_count=Count('likes')).order_by('-like_count')
#         if 'most_bookmarked' in value:
#             queryset = queryset.annotate(bookmark_count=Count('bookmarks')).order_by('-bookmark_count')
#         return queryset