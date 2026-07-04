"""
BaseTrue Pattern Engine URL Configuration
"""

from django.urls import path
from . import views

app_name = 'baseture_engine'

urlpatterns = [
    # Dashboard
    path('', views.tier_dashboard, name='dashboard'),
    
    # API Endpoints - Tier Generation
    path('api/generate/', views.api_generate_tier, name='api_generate'),
    path('api/save/', views.api_save_generated_tier, name='api_save'),
    path('api/list/', views.api_list_generated_tiers, name='api_list'),
    path('api/approve/<int:tier_id>/', views.api_approve_tier, name='api_approve'),
    
    # API Endpoints - Hierarchy Generation
    path('api/hierarchy/generate-svem/', views.api_generate_svem_branches, name='api_generate_svem'),
    path('api/hierarchy/generate-cccp/', views.api_generate_cccp_compartments, name='api_generate_cccp'),
    path('api/hierarchy/generate-dchd/', views.api_generate_dchd_subcells, name='api_generate_dchd'),
    path('api/hierarchy/tree/<int:root_id>/', views.api_get_hierarchy_tree, name='api_hierarchy_tree'),
]
