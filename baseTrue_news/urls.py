from django.urls import path

from . import views


app_name = "baseTrue_news"

urlpatterns = [
    path("", views.NewsletterHomeView.as_view(), name="index"),
    path("subscribe/", views.NewsletterSignupView.as_view(), name="subscribe"),
    path("unsubscribe/<uuid:token>/", views.NewsletterUnsubscribeView.as_view(), name="unsubscribe"),
    path("archive/", views.IssueArchiveView.as_view(), name="archive"),
    path("issue/<int:year>/<int:month>/", views.IssueDetailView.as_view(), name="issue_detail"),
]
