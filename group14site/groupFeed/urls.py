from django.urls import path, include
from . import views

urlpatterns = [
    path('<int:group_id>/', views.group_feed, name='group_feed'),
    path('detail/<int:recommendation_post_id>/', views.group_detail, name='group_detail'),
    path('detail/<int:recommendation_post_id>/add_comment', views.add_comment, name='add_comment'),
    path('detail/<int:recommendation_post_id>/upvote', views.handle_upvote, name='upvote'),
    path('detail/<int:recommendation_post_id>/downvote', views.handle_downvote, name='downvote'),
    path('group/delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('comment/delete/<int:comment_id>/<int:post_id>/', views.admin_delete_comment, name='admin_delete_comment'),

]
