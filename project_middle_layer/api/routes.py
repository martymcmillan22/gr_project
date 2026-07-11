from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProjectCreationWizardCompileAPIView,
    ProjectCreationWizardStartAPIView,
    ProjectCreationWizardTagsAPIView,
    ProjectMiddleLayerCompileAPIView,
    ProjectNodeViewSet,
)

router = DefaultRouter()
router.register(r"nodes", ProjectNodeViewSet, basename="project-middle-layer-nodes")

urlpatterns = [
    path("compile/", ProjectMiddleLayerCompileAPIView.as_view(), name="project-middle-layer-compile"),
    path("wizard/start/", ProjectCreationWizardStartAPIView.as_view(), name="project-middle-layer-wizard-start"),
    path("wizard/<str:wizard_id>/tags/", ProjectCreationWizardTagsAPIView.as_view(), name="project-middle-layer-wizard-tags"),
    path("wizard/<str:wizard_id>/compile/", ProjectCreationWizardCompileAPIView.as_view(), name="project-middle-layer-wizard-compile"),
    path("", include(router.urls)),
]
