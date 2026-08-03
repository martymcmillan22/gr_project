from django.urls import path

from .views import boundary_health_view
from .views import semantic_activation_view


urlpatterns = [
    path("health/", boundary_health_view, name="platform-semantic-health"),
    path("activation/", semantic_activation_view, name="platform-semantic-activation"),
]
