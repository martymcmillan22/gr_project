from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CrossReferenceReadOnlyViewSet, IdeaCaptureAPIView, ProjectActivationAPIView, RRCardSpecAPIView, RRDashboardAPIView, RRIndustryMapAPIView, RRNodeDetailAPIView, RROperatingStackAPIView, RRSemanticActionEngineAPIView, RRSemanticIntelligenceAPIView, RRVAGuidanceAPIView, SeedPromotionAPIView

router = DefaultRouter()
router.register(r"cross-reference", CrossReferenceReadOnlyViewSet, basename="cross-reference")

urlpatterns = [
    path("api/capture/", IdeaCaptureAPIView.as_view(), name="idea-capture"),
    path("api/promote-seed/", SeedPromotionAPIView.as_view(), name="seed-promote"),
    path("api/activate-project/", ProjectActivationAPIView.as_view(), name="project-activate"),
    path("api/rr/dashboard/", RRDashboardAPIView.as_view(), name="rr-dashboard"),
    path("api/rr/industry-map/", RRIndustryMapAPIView.as_view(), name="rr-industry-map"),
    path("api/rr/card-spec/", RRCardSpecAPIView.as_view(), name="rr-card-spec"),
    path("api/rr/va-guidance/", RRVAGuidanceAPIView.as_view(), name="rr-va-guidance"),
    path("api/rr/operating-stack/", RROperatingStackAPIView.as_view(), name="rr-operating-stack"),
    path("api/rr/semantic-intelligence/", RRSemanticIntelligenceAPIView.as_view(), name="rr-semantic-intelligence"),
    path("api/rr/semantic-actions/execute/", RRSemanticActionEngineAPIView.as_view(), name="rr-semantic-actions-execute"),
    path("api/rr/nodes/<int:business_id>/", RRNodeDetailAPIView.as_view(), name="rr-node-detail"),
    path("api/", include(router.urls)),
]
