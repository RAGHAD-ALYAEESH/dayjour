from django.urls import path
from . import views

urlpatterns = [
    path('', views.collaborations, name='collaborations'),
    path('<int:pk>/', views.collaboration_detail, name='collaboration_detail'),
    path('<int:pk>/upload/', views.upload_collaboration_data, name='upload_collaboration_data'),
    path('<int:pk>/delete/', views.delete_collaboration, name='delete_collaboration'),
    path('new/', views.new_collaboration, name='new_collaboration'),
    path('invite/accept/<uuid:token>/', views.accept_invite, name='accept_invite'),
    path('invite/reject/<uuid:token>/', views.reject_invite, name='reject_invite'),
]