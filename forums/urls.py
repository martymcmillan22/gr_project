from django.urls import path

from .views import (
    CityForumView,
    ForumAccessView,
    InternationalForumView,
    NationalForumView,
    StateForumView,
)

app_name = "forums"

urlpatterns = [
    path("access/<slug:forum_key>/", ForumAccessView.as_view(), name="access"),
    path("city/", CityForumView.as_view(), name="city"),
    path("state/", StateForumView.as_view(), name="state"),
    path("national/", NationalForumView.as_view(), name="national"),
    path("global/", InternationalForumView.as_view(), name="global"),
]
