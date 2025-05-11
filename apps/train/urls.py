from django.urls import path
from . import views

urlpatterns = [
    path('collaboration/<int:pk>/train/', views.trainLocalmodel, name='train_model'),
    path('collaboration/<int:pk>/insight/', views.model_insights, name='model_insights'),
    path('collaboration/<int:pk>/download/', views.download_shap_pdf, name='download_shap_pdf'),

    path('train/', views.trainLocalmodel, name='train_local_model'),
    path('models/', views.view_trained_models, name='view_trained_models'),
    path('insights/', views.model_insights, name='model_insights'),
]