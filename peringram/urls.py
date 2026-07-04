from django.urls import path

from .views import PIPView

app_name = "peringram"

urlpatterns = [
    path("", PIPView.as_view(), name="dashboard"),
]
