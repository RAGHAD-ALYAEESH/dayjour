from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='user_login'),
    path('signup/', views.signin_view, name='signin_view'),
    path('dashboard/', views.dashboard, name='dashboard'),
]