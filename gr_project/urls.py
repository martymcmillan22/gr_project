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
from platform_core.activation import phase4_activation_view
from platform_core.activation import phase4_orchestration_view

from polish.views import (
    TaskManagerAdminView,
    task_manager_activity_api,
    task_manager_assignment_timeline_api,
    task_manager_metrics_api,
)
from homepage_backend.views import HomepageAppView


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
    path('admin/task-manager/assignments/<int:assignment_id>/timeline/', task_manager_assignment_timeline_api, name='task-manager-assignment-timeline-api'),
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
    path('ispe/', HomepageAppView.as_view(), name='ispe-app'),
    path('platform/reference/', include('platform_reference.urls')),
    path('platform/semantic/', include('platform_semantic.urls')),
    path('platform/quadrant/', include('platform_quadrant.urls')),
    path('platform/activation/', phase4_activation_view, name='platform-phase4-activation'),
    path('platform/orchestration/', phase4_orchestration_view, name='platform-phase4-orchestration'),
    path('ispe/', include('ispe.urls')),
    path('platform/billing/', include('platform_billing.urls')),
    path('storytelling-dashboard/', include('storytelling_dashboard.urls')),
    path('baseture-engine/', include('baseture_engine.urls')),
    path('diagnostics/', HomepageAppView.as_view(), name='diagnostics'),
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
