from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload, name='upload_data'),
    path('uploaded/', views.uploaded_data, name='uploaded_data'),
    path('delete_file/<int:pk>/', views.delete_uploaded_file, name='delete_uploaded_file'),
]