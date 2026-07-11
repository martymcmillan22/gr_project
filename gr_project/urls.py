"""trivia URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from polish.views import TaskManagerAdminView, task_manager_activity_api, task_manager_metrics_api


urlpatterns = [
    path(
        'admin/task-manager/',
        include(
            (
                [path('', TaskManagerAdminView.as_view(), name='index')],
                'task-manager-admin',
            ),
            namespace='task-manager-admin',
        ),
    ),
    path('admin/task-manager/metrics/', task_manager_metrics_api, name='task-manager-metrics-api'),
    path('admin/task-manager/activity/', task_manager_activity_api, name='task-manager-activity-api'),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('home.urls')),
    path("news/", include("polls.urls")),
    path('center/', include("center.urls")),
    path('domain/', include("domain.urls")),
    path('polish/', include("polish.urls")),
    path('peringram/', include("peringram.urls")),
    path('forums/', include("forums.urls")),
    path('career/', include('career_app.urls')),
    path('basetruenews/', include('baseTrue_news.urls')),
    path('seeds/', include('seeds.urls')),
    path('contracts/', include('platform_core.urls')),
    path('storytelling-dashboard/', include('storytelling_dashboard.urls')),
    path('baseture-engine/', include('baseture_engine.urls')),
    path('btif/api/', include(('ontology.urls', 'ontology'), namespace='btif')),
    path('', include('twist.urls')),
    path('', include('povs.urls')),

    path('homepage/', include('homepage_backend.urls')),
    path('support/', include('support.urls')),
    path('project-middle-layer/', include('project_middle_layer.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # https://docs.djangoproject.com/en/4.2/howto/static-files/#serving-uploaded-files-in-development

if 'debug_toolbar' in settings.INSTALLED_APPS:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
