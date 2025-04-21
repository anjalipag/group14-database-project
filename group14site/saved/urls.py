from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("group/feed/", include("groupFeed.urls")),
    path("omdb/", views.omdb_api, name="omdb_api"),
]