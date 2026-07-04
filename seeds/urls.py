from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CrossReferenceReadOnlyViewSet, IdeaCaptureAPIView

router = DefaultRouter()
router.register(r"cross-reference", CrossReferenceReadOnlyViewSet, basename="cross-reference")

urlpatterns = [
    path("api/capture/", IdeaCaptureAPIView.as_view(), name="idea-capture"),
    path("api/", include(router.urls)),
]
