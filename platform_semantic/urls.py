from django.urls import path

from .views import boundary_health_view
from .views import semantic_color_preview_view
from .views import semantic_activation_view
from .views import semantic_subject_grid_view


urlpatterns = [
    path("health/", boundary_health_view, name="platform-semantic-health"),
    path("activation/", semantic_activation_view, name="platform-semantic-activation"),
    path("color-preview/", semantic_color_preview_view, name="platform-semantic-color-preview"),
    path("subject-grid/", semantic_subject_grid_view, name="platform-semantic-subject-grid"),
]
