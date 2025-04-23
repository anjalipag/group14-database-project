from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("group/feed/", include("groupFeed.urls")),
    path('delete_rec/<int:rec_id>/', views.delete_rec, name='delete_rec'),

]