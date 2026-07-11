from django.urls import path

from .views import ProjectMiddleLayerStatusView

app_name = "project_middle_layer"

urlpatterns = [
    path("", ProjectMiddleLayerStatusView.as_view(), name="status"),
]
