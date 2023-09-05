import django_filters
from django.db.models import Count, Q, Subquery
from app.models import *
from django.db.models import Count, F
from rest_framework import filters
from rest_framework import generics
from django_filters import rest_framework as django_filters

# Define a custom filter for the Article model
class ArticleFilter(django_filters.FilterSet):
    class Meta:
        model = Article
        fields = ['status']  # Add other filter fields if needed

    # Custom filter for articles ordered by rating in ascending order
    rated = django_filters.OrderingFilter(
        fields=('commentbase__rating',),
        field_labels={'commentbase__rating': 'Rating'},
    )

    # Custom filter for articles ordered by rating in descending order
    lowest_rated = django_filters.OrderingFilter(
        fields=('-commentbase__rating',),
        field_labels={'-commentbase__rating': 'Lowest Rating'},
    )

    # Custom filter for articles ordered by creation date in descending order
    recent = django_filters.OrderingFilter(
        fields=('-Public_date',),
        field_labels={'-Public_date': 'Most Recent'},
    )

    # Custom filter for articles ordered by creation date in ascending order
    least_recent = django_filters.OrderingFilter(
        fields=('Public_date',),
        field_labels={'Public_date': 'Least Recent'},
    )

    # Custom filter for articles ordered by views in descending order
    viewed = django_filters.OrderingFilter(
        fields=('-views',),
        field_labels={'-views': 'Most Viewed'},
    )

    # Custom filter for articles ordered by views in ascending order
    least_viewed = django_filters.OrderingFilter(
        fields=('views',),
        field_labels={'views': 'Least Viewed'},
    )

    # Custom filter for articles ordered by favorite count in descending order
    favourite = django_filters.OrderingFilter(
        fields=('favourite_count',),
        field_labels={'favourite_count': 'Most Favorited'},
    )

    # Custom filter for articles ordered by favorite count in ascending order
    least_favourite = django_filters.OrderingFilter(
        fields=('-favourite_count',),
        field_labels={'-favourite_count': 'Least Favorited'},
    )
     
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