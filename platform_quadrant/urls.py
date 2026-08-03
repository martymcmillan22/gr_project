from django.urls import path

from .views import boundary_health_view
from .views import quadrant_activation_view


urlpatterns = [
    path("health/", boundary_health_view, name="platform-quadrant-health"),
    path("activation/", quadrant_activation_view, name="platform-quadrant-activation"),
]
