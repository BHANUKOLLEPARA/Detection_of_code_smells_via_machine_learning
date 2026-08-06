"""
Detector App URL Configuration
"""

from django.urls import path
from . import views

app_name = 'detector'  # This defines the namespace

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('static-mode/', views.static_mode, name='static_mode'),
    path('dynamic-mode/', views.dynamic_mode, name='dynamic_mode'),
    path('training-results/', views.training_results, name='training_results'),
    path('prediction-results/<int:job_id>/', views.prediction_results, name='prediction_results'),
    path('history/', views.history, name='history'),
    path('download-report/<int:job_id>/', views.download_report, name='download_report'),
    path('delete-analysis/<int:job_id>/', views.delete_analysis, name='delete_analysis'),
    path('api-docs/', views.api_docs, name='api_docs'),
    path('about/', views.about, name='about'),
]