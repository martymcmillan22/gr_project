from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.apps import apps
from django.db import models
from django.db.models import CharField
from django.urls import reverse


class User(AbstractUser):
    """
    Create a custom User class.
    - Not all users have a first and last name, so use a single name field
    - Users should be able to log in with their email, so make it unique
    """
    name = CharField(max_length=255)
    email = models.EmailField('Email address', unique=True)
    avatar = models.ImageField(upload_to='avatars', blank=True, null=True)
    SUBSCRIPTION_FREE = "free"
    SUBSCRIPTION_PREMIUM_STARTER = "premium_starter"
    SUBSCRIPTION_PREMIUM_PRO = "premium_pro"
    SUBSCRIPTION_PREMIUM_ENTERPRISE = "premium_enterprise"
    SUBSCRIPTION_CHOICES = (
        (SUBSCRIPTION_FREE, "Free"),
        (SUBSCRIPTION_PREMIUM_STARTER, "Premium Starter"),
        (SUBSCRIPTION_PREMIUM_PRO, "Premium Pro"),
        (SUBSCRIPTION_PREMIUM_ENTERPRISE, "Premium Enterprise"),
    )
    subscription_tier = models.CharField(max_length=32, choices=SUBSCRIPTION_CHOICES, default=SUBSCRIPTION_FREE)

    USERNAME_FIELD = 'email'                # Log in with email (instead of username)
    REQUIRED_FIELDS = ['name', 'username']  # Require these when creating a superuser

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.
        """
        return reverse("users:detail", kwargs={"username": self.username})

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return settings.STATIC_URL + 'images/avatar.png'

    def is_premium_subscriber(self):
        return self.subscription_tier != self.SUBSCRIPTION_FREE

    def get_storage_quota_bytes(self):
        quota_by_tier = {
            self.SUBSCRIPTION_FREE: 10 * 1024 * 1024 * 1024,
            self.SUBSCRIPTION_PREMIUM_STARTER: 50 * 1024 * 1024 * 1024,
            self.SUBSCRIPTION_PREMIUM_PRO: 200 * 1024 * 1024 * 1024,
            self.SUBSCRIPTION_PREMIUM_ENTERPRISE: 1024 * 1024 * 1024 * 1024,
        }
        return quota_by_tier.get(self.subscription_tier, quota_by_tier[self.SUBSCRIPTION_FREE])

    def get_upload_size_cap_bytes(self):
        cap_by_tier = {
            self.SUBSCRIPTION_FREE: 10 * 1024 * 1024,
            self.SUBSCRIPTION_PREMIUM_STARTER: 25 * 1024 * 1024,
            self.SUBSCRIPTION_PREMIUM_PRO: 100 * 1024 * 1024,
            self.SUBSCRIPTION_PREMIUM_ENTERPRISE: 250 * 1024 * 1024,
        }
        return cap_by_tier.get(self.subscription_tier, cap_by_tier[self.SUBSCRIPTION_FREE])

    def get_storage_used_bytes(self):
        attachment_model = apps.get_model("polish", "TaskAssignmentAttachment")
        return attachment_model.objects.filter(uploaded_by=self).aggregate(total=models.Sum("file_size_bytes")).get("total") or 0


class BillingWebhookEvent(models.Model):
    STATUS_RECEIVED = "received"
    STATUS_PROCESSED = "processed"
    STATUS_IGNORED = "ignored"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_RECEIVED, "Received"),
        (STATUS_PROCESSED, "Processed"),
        (STATUS_IGNORED, "Ignored"),
        (STATUS_FAILED, "Failed"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="billing_webhook_events",
    )
    provider = models.CharField(max_length=32, default="generic")
    provider_event_id = models.CharField(max_length=128, blank=True)
    idempotency_key = models.CharField(max_length=128)
    event_type = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_RECEIVED)
    signature_valid = models.BooleanField(default=False)
    target_tier = models.CharField(max_length=32, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "idempotency_key"),
                name="ux_billing_webhook_event_provider_idempotency",
            )
        ]

    def __str__(self):
        return f"{self.provider}:{self.event_type or 'unknown'}:{self.status}"


class BillingCheckoutIntent(models.Model):
    STATUS_CREATED = "created"
    STATUS_SESSION_CREATED = "session_created"
    STATUS_FAILED = "failed"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = (
        (STATUS_CREATED, "Created"),
        (STATUS_SESSION_CREATED, "Session Created"),
        (STATUS_FAILED, "Failed"),
        (STATUS_COMPLETED, "Completed"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_checkout_intents",
    )
    provider = models.CharField(max_length=32, default="stripe")
    requested_tier = models.CharField(max_length=32)
    idempotency_key = models.CharField(max_length=128)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_CREATED)
    provider_session_id = models.CharField(max_length=128, blank=True)
    checkout_url = models.URLField(blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "provider", "idempotency_key"),
                name="ux_billing_checkout_intent_user_provider_idempotency",
            )
        ]

    def __str__(self):
        return f"{self.provider}:{self.requested_tier}:{self.status}"