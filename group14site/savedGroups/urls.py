from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.my_groups, name="my_groups"),
    path("adminview/<int:group_id>/", views.admin_view, name="admin_view"),
    path("adminview/<int:group_id>/manage", views.manage_requests, name="manage_requests"),
    path("group/feed/", include("groupFeed.urls")),
]