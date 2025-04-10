from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.my_groups, name="my_groups"),
    path("group/feed/", include("groupFeed.urls"))
]