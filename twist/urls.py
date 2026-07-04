#urls
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import CreativeIdeaViewSet, TwistEntryView, TwistIdeaDeleteView, TwistIdeaEditView, TwistTokenView

router = DefaultRouter()
router.register(r'ideas', CreativeIdeaViewSet, basename='ideas')

urlpatterns = [
    path('twist/', TwistEntryView.as_view(), name='twist-entry'),
    path('twist/token/', TwistTokenView.as_view(), name='twist-token'),
    path('twist/ideas/<int:pk>/edit/', TwistIdeaEditView.as_view(), name='twist-idea-edit'),
    path('twist/ideas/<int:pk>/delete/', TwistIdeaDeleteView.as_view(), name='twist-idea-delete'),
    path('api/', include(router.urls)),
    path('api/login/', obtain_auth_token), # Sending credentials here returns a token for flutter
]