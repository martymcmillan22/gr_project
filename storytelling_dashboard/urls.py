from django.urls import path
from . import views

app_name = 'storytelling_dashboard'

urlpatterns = [
    # Web Views
    path('', views.dashboard, name='dashboard'),
    path('story/<int:entry_id>/', views.story_detail, name='story_detail'),
    
    # API Endpoints
    path('api/stories/', views.api_stories, name='api_stories'),
    path('api/story/<int:entry_id>/', views.api_story, name='api_story'),
    path('api/story/<int:entry_id>/save/', views.api_story_save, name='api_story_save'),
    path('api/story/<int:entry_id>/validate/', views.api_story_validate, name='api_story_validate'),
    path('api/story/<int:entry_id>/git-history/', views.api_git_history, name='api_git_history'),
    path('api/git/push/', views.api_git_push, name='api_git_push'),
    path('api/git/status/', views.api_git_status, name='api_git_status'),
]
