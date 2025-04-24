from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_recommendations, name='user_recommendations'),
    path('comments/<int:recommendation_post_id>/', views.comment_detail, name='user_reccs_comments'),
    path('delete_my_post/<int:recommendation_post_id>/', views.delete_my_post, name='delete_my_post'),
]