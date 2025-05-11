from django.urls import path
from . import views

urlpatterns = [
    path('settings/', views.account_settings, name='account_settings'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
]