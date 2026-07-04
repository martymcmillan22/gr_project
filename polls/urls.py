from django.urls import path
from .views import ArticleMonthArchiveView
from . import views

app_name = "polls"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("<int:question_id>/vote/", views.vote, name="vote"),
    path("articles/detail/<int:pk>/", views.ArticleDetailView.as_view(), name="article_detail"),
    path("articles/<int:year>/", views.year_archive, name="archive_year"),
    path("articles/<int:year>/details/", views.Year_archive_detailView.as_view(), name="archive_year_detail"),
    path('articles/<int:year>/<int:month>/', ArticleMonthArchiveView.as_view(), name="archive_month"),
]

