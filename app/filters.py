# import django_filters
# from django.db.models import Count, Q, Subquery

# from app.models import Article, CommentBase,LikeBase

# class ArticleFilter(django_filters.FilterSet):
#     most_rated = django_filters.BooleanFilter(method='filter_most_rated')
#     most_viewed = django_filters.BooleanFilter(method='filter_most_viewed')
#     most_commented = django_filters.BooleanFilter(method='filter_most_commented')

#     class Meta:
#         model = Article
#         fields = []

#     def filter_most_rated(self, queryset, name, value):
#       queryset = queryset.filter(rating__gt=3.00).order_by('-rating')
#       return queryset

#     def filter_most_viewed(self, queryset, name, value):  
#       queryset = queryset.order_by('-views')
#       return queryset

#     def filter_most_commented(self, queryset, name, value):
#       queryset = queryset.order_by('-comments_count')
#       return queryset
     
# class ReviewFilter(django_filters.FilterSet):
#    most_liked = django_filters.BooleanFilter(method='filter_most_liked')
#    most_liked = django_filters.BooleanFilter(method='filter_most_liked')
#    most_commented = django_filters.BooleanFilter(method='filter_most_commented')
   
#    class Meta:
#       model = Review
#       fields = []
      
#    def filter_most_liked(self, queryset, name, value):
#       liked_query= LikeReview.objects.filter(value='like')
#       queryset = queryset.annotate(like_count=Subquery(liked_query))
#       return queryset
       
#    def filter_most_disliked(self, queryset, name, value):
      
#       disliked_query= LikeReview.objects.filter(value='unlike')
#       queryset = queryset.annotate(like_count=Subquery(disliked_query))
#       return queryset

#    def filter_most_commented(self, queryset, name, value):
#       if value:
#          queryset = queryset.order_by('-comments_count')
#       return queryset
   
# class DecisionFilter(django_filters.FilterSet):
#    most_liked = django_filters.BooleanFilter(method='filter_most_liked')
#    most_disliked = django_filters.BooleanFilter(method='filter_most_disliked')
#    most_commented = django_filters.BooleanFilter(method='filter_most_commented')
   
#    class Meta:
#       model = Decision
#       fields = []
      
#    def filter_most_liked(self, queryset, name, value):
#       liked_query= LikeDecision.objects.filter(value='like')
#       queryset = queryset.annotate(like_count=Subquery(liked_query))
#       return queryset
       
#    def filter_most_disliked(self, queryset, name, value):
      
#       disliked_query= LikeDecision.objects.filter(value='unlike')
#       queryset = queryset.annotate(like_count=Subquery(disliked_query))
#       return queryset

#    def filter_most_commented(self, queryset, name, value):
#       if value:
#          queryset = queryset.order_by('-comments_count')
#       return queryset