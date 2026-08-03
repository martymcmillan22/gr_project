from django.urls import path

from .views import boundary_health_view


urlpatterns = [
    path("health/", boundary_health_view, name="platform-billing-health"),
]
