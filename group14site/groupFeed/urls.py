from django.urls import path
from . import views

urlpatterns = [
    path('<int:group_id>/', views.group_feed, name='group_feed'),
    path('detail/<int:recommendation_post_id>/', views.group_detail, name='group_detail'),
    path('detail/<int:recommendation_post_id>/<int:group_id>/', views.group_detail, name='group_detail'),
    path('add_recommendation/<int:group_id>/', views.add_recommendation, name='add_recommendation'),
    path('detail/<int:recommendation_post_id>/add_comment', views.add_comment, name='add_comment'),
    path('detail/<int:recommendation_post_id>/upvote', views.handle_upvote, name='upvote'),
    path('detail/<int:recommendation_post_id>/downvote', views.handle_downvote, name='downvote'),
    path('search/', views.search_deezer, name='search_deezer'),
    path('search_books/', views.search_openlibrary, name='search_openlibrary'),
    path('search_movies/', views.search_omdb_movies, name='search_omdb_movies'),
    path('search_shows/', views.search_omdb_shows, name='search_omdb_shows'),
    path('saved/<int:recommendation_post_id>/<int:posted_by_id>/<int:group_id>', views.save_recc,
         name='save_recc'),
    path('saved/detail/<int:recommendation_post_id>/<int:posted_by_id>/', views.save_recc_det, name='save_recc_det'),

    path('group/delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('comment/delete/<int:comment_id>/<int:post_id>/', views.admin_delete_comment, name='admin_delete_comment'),
    path('group_image/<int:group_id>/', views.serve_group_image, name='serve_group_image'),
    path('leave_group/<int:group_id>/', views.leave_group, name='leave_group'),
    path('delete_group/<int:group_id>/', views.delete_group, name='delete_group'),
]
