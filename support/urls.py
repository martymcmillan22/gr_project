from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("", views.support_page, name="support_page"),
    path("feedback/submit/", views.submit_feedback, name="submit_feedback"),
]
