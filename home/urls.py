from django.urls import path

from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='index'),
    path('slides/', views.SlidesHubView.as_view(), name='slides-hub'),
    path('workflow/btsrl/', views.BTSRLView.as_view(), name='btsrl'),
    path('slides/architecture/', views.ArchitectureSlidesView.as_view(), name='architecture-slides'),
    path('slides/executive/', views.ExecutiveSlidesView.as_view(), name='executive-slides'),
]