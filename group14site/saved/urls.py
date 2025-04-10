from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("details/<int:rec_id>/", views.see_recommendation_details, name="saved_rec_details"),
    path("details/<int:rec_id>/upvote", views.handle_upvote, name="upvote"),
    path("details/<int:rec_id>/downvote", views.handle_downvote, name="downvote"),
]