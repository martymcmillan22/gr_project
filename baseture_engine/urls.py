"""
BaseTrue Pattern Engine URL Configuration
"""

from django.urls import path
from . import views

app_name = 'baseture_engine'

urlpatterns = [
    # Dashboard
    path('', views.tier_dashboard, name='dashboard'),
    
    # API Endpoints
    path('api/generate/', views.api_generate_tier, name='api_generate'),
    path('api/save/', views.api_save_generated_tier, name='api_save'),
    path('api/list/', views.api_list_generated_tiers, name='api_list'),
    path('api/approve/<int:tier_id>/', views.api_approve_tier, name='api_approve'),
]
