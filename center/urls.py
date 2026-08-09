from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "center"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("grid/<slug:slug>/", views.CellDetailView.as_view(), name="cell_detail"),
    path("insufficient-tier/", views.InsufficientTierView.as_view(), name="insufficient_tier"),
    path("boards/corporation-admin/", views.CorporationAdminView.as_view(), name="corporation_admin"),
    path("boards/corporation-btif/", RedirectView.as_view(pattern_name="center:corporation_admin", permanent=False), name="corporation_btif"),
    path("boards/museum-social/", views.MuseumSocialView.as_view(), name="museum_social"),
    path("boards/garden-board/", views.GardenBoardView.as_view(), name="garden_board"),
    path("boards/meta-interface/", views.MetaInterfaceView.as_view(), name="meta_interface"),
]
