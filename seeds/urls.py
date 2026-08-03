from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CrossReferenceReadOnlyViewSet, IdeaCaptureAPIView, ProjectActivationAPIView, SeedPromotionAPIView

router = DefaultRouter()
router.register(r"cross-reference", CrossReferenceReadOnlyViewSet, basename="cross-reference")

urlpatterns = [
    path("api/capture/", IdeaCaptureAPIView.as_view(), name="idea-capture"),
    path("api/promote-seed/", SeedPromotionAPIView.as_view(), name="seed-promote"),
    path("api/activate-project/", ProjectActivationAPIView.as_view(), name="project-activate"),
    path("api/", include(router.urls)),
]
