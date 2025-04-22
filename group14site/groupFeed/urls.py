from django.urls import path
from . import views

urlpatterns = [
    path('<int:group_id>/', views.group_feed, name='group_feed'),
    path('detail/<int:recommendation_post_id>/', views.group_detail, name='group_detail'),
    path('add_recommendation/<int:group_id>/', views.add_recommendation, name='add_recommendation'),
    path('detail/<int:recommendation_post_id>/add_comment', views.add_comment, name='add_comment'),
    path('detail/<int:recommendation_post_id>/upvote', views.handle_upvote, name='upvote'),
    path('detail/<int:recommendation_post_id>/downvote', views.handle_downvote, name='downvote'),
    path('search/', views.search_deezer, name='search_deezer'),
    path('search_books/', views.search_openlibrary, name='search_openlibrary'),
]
