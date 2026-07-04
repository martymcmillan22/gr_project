from django.urls import path

from .views import (
    UserDetailView,
    UserRedirectView,
    UserSignUp,
    BillingCheckoutSessionCreateView,
    BillingWebhookView,
    SubscriptionUpgradeView,
    UserUpdateView,
    ListView,
)

app_name = "users"
urlpatterns = [
    path("signup/", view=UserSignUp.as_view(), name="signup"),
    path("billing/checkout/session/", view=BillingCheckoutSessionCreateView.as_view(), name="billing-checkout-session"),
    path("billing/webhook/", view=BillingWebhookView.as_view(), name="billing-webhook"),
    path("subscription/upgrade/", view=SubscriptionUpgradeView.as_view(), name="subscription-upgrade"),
    path("redirect/", view=UserRedirectView.as_view(), name="redirect"),
    path("update/", view=UserUpdateView.as_view(), name="update"),
    path("<str:username>/", view=UserDetailView.as_view(), name="detail"),
    path("my", view=UserDetailView.as_view(), name="my-profile"),
    path("", view=ListView.as_view(), name="list"),
]
