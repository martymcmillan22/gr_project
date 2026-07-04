from django.urls import path
from .views import CreateExpoFactView, EditExpoFactView, ExpoFactDetailView, PovsHomeView

urlpatterns = [
    path('povs/', PovsHomeView.as_view(), name='povs-home'),
    path('povs/create/', CreateExpoFactView.as_view(), name='povs-create'),
    path('povs/<int:pk>/', ExpoFactDetailView.as_view(), name='povs-detail'),
    path('povs/<int:pk>/edit/', EditExpoFactView.as_view(), name='povs-edit'),
]
