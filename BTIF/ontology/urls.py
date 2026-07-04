from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from ontology.auth_views import CurrentUserView, RegisterView, RevokeTokenView
from ontology.views import (
    BranchViewSet,
    LatticeMapExportView,
    IndustryViewSet,
    LinearHierarchyGenerateView,
    LatticeMapView,
    SubjectViewSet,
    SubIndustryViewSet,
    TemporalSlotViewSet,
)

router = DefaultRouter()
router.register("subjects", SubjectViewSet, basename="subject")
router.register("branches", BranchViewSet, basename="branch")
router.register("industries", IndustryViewSet, basename="industry")
router.register("sub-industries", SubIndustryViewSet, basename="subindustry")
router.register("temporal-slots", TemporalSlotViewSet, basename="temporalslot")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/token/", obtain_auth_token, name="auth-token"),
    path("auth/me/", CurrentUserView.as_view(), name="auth-me"),
    path("auth/token/revoke/", RevokeTokenView.as_view(), name="auth-token-revoke"),
    path("generate-linear-hierarchy/", LinearHierarchyGenerateView.as_view(), name="generate-linear-hierarchy"),
    path("", include(router.urls)),
    path("lattice-map/", LatticeMapView.as_view(), name="lattice-map"),
    path("lattice-map/export/", LatticeMapExportView.as_view(), name="lattice-map-export"),
]