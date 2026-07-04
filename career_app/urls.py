from django.urls import path
from . import views

urlpatterns = [
    path('', views.search_careers, name='search_careers'),
    path('clear-cache/', views.clear_career_cache, name='clear_career_cache'),
    path('export-pdf/', views.export_careers_pdf, name='export_careers_pdf'),
    path('export-csv/', views.export_careers_csv, name='export_careers_csv'),
    path('api/filter-presets/', views.filter_presets, name='filter_presets'),
    path('api/filter-presets/<int:preset_id>/', views.filter_preset_detail, name='filter_preset_detail'),
]
