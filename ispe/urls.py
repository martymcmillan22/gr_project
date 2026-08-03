from django.urls import path

from .views import ispe_activation_view


app_name = "ispe"

urlpatterns = [
    path("activation/", ispe_activation_view, name="activation"),
]
