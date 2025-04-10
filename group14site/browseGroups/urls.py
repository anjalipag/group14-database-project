from django.urls import path
from . import views

urlpatterns = [
    path('', views.browse_groups, name='browse_groups'),
]
