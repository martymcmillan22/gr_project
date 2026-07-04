from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    HomepageActionViewSet,
    HomepageAppView,
    HomepageBackendItemViewSet,
    HomepageFlowViewSet,
    HomepageOverviewAPIView,
    HomepagePresentationSlidesAPIView,
    HomepagePreferenceViewSet,
    HomepageTaskViewSet,
)

router = DefaultRouter()
router.register(r"items", HomepageBackendItemViewSet, basename="homepage-items")
router.register(r"tasks", HomepageTaskViewSet, basename="homepage-tasks")
router.register(r"flows", HomepageFlowViewSet, basename="homepage-flows")
router.register(r"preferences", HomepagePreferenceViewSet, basename="homepage-preferences")
router.register(r"actions", HomepageActionViewSet, basename="homepage-actions")

urlpatterns = [
    path("", HomepageAppView.as_view(), name="homepage-app"),
    path("api/overview/", HomepageOverviewAPIView.as_view(), name="homepage-overview"),
    path("api/presentation-slides/", HomepagePresentationSlidesAPIView.as_view(), name="homepage-presentation-slides"),
    path("api/", include(router.urls)),
]
