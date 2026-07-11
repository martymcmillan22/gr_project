from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProjectMiddleLayerCompileAPIView, ProjectNodeViewSet

router = DefaultRouter()
router.register(r"nodes", ProjectNodeViewSet, basename="project-middle-layer-nodes")

urlpatterns = [
    path("compile/", ProjectMiddleLayerCompileAPIView.as_view(), name="project-middle-layer-compile"),
    path("", include(router.urls)),
]
