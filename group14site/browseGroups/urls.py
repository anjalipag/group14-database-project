from django.urls import path
from . import views

urlpatterns = [
    path('', views.browse_groups, name='browse_groups'),
    path('<int:group_id>/', views.send_join_request, name='send_join_request'),
    path('group_image/<int:group_id>/', views.serve_group_image, name='serve_group_image'),
]