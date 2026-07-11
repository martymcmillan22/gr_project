from django.urls import include, path

from .views import ProjectMiddleLayerStatusView

app_name = "project_middle_layer"

urlpatterns = [
    path("", ProjectMiddleLayerStatusView.as_view(), name="status"),
    path("api/", include("project_middle_layer.api.routes")),
]
