from django.urls import path

from . import views

app_name = "domain"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("edit/", views.EditView.as_view(), name="edit"),
    path("grid/<slug:slug>/", views.CellDetailView.as_view(), name="cell_detail"),
]
