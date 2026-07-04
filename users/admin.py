"""
Advanced Django Admin
https://docs.djangoproject.com/en/4.2/ref/contrib/admin/
"""
from django.contrib import admin
from django.contrib.auth import admin as auth_admin, get_user_model
from django.contrib.auth.models import Group

from .forms import UserChangeForm, UserCreationForm
from .models import BillingCheckoutIntent, BillingWebhookEvent

User = get_user_model()  # get the user model as defined by AUTH_USER_MODEL in settings

POLISH_ADMIN_GROUP_NAME = "polish_admin"


class PolishAdminStatusFilter(admin.SimpleListFilter):
    title = "polish admin"
    parameter_name = "polish_admin"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Yes"),
            ("no", "No"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(groups__name=POLISH_ADMIN_GROUP_NAME).distinct()
        if value == "no":
            return queryset.exclude(groups__name=POLISH_ADMIN_GROUP_NAME)
        return queryset


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    """
    Subclass the original UserAdmin
    Uses name field instead of first_name and last name
    Makes email more visible and required during creation
    """
    add_form = UserCreationForm

    # Fieldsets - sections/fields to show in forms (only the change form in this case)
    # https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.fieldsets
    fieldsets = (("User", {"fields": ("name", "avatar")}),) + tuple(auth_admin.UserAdmin.fieldsets)

    # List display - fields to show in the list display
    list_display = (
        "username",
        "email",
        "name",
        "subscription_tier",
        "is_polish_admin_member",
        "is_superuser",
        "is_staff",
        "is_active",
    )

    # Search fields - fields to search on in search bar
    search_fields = ("name", "username", "email")

    # List filter - fields to filter on in the right sidebar
    list_filter = (
        "subscription_tier",
        PolishAdminStatusFilter,
        "is_superuser",
        "is_staff",
        "is_active",
    )

    # The original UserAdmin shows a different set of fields when creating a new User
    # Ours requires name and email as well as username and password
    add_fieldsets = (
        (None, {
            "fields": ("username", "name", "email", "password1", "password2", "is_staff")}
         ),
    )

    # Ordering - fields to order by in the list display
    ordering = ("email",)
    actions = (
        "grant_executive_slides_access",
        "revoke_executive_slides_access",
        "grant_polish_admin_access",
        "revoke_polish_admin_access",
    )

    executive_group_name = "executive_slides_access"

    def _get_executive_group(self):
        group, _ = Group.objects.get_or_create(name=self.executive_group_name)
        return group

    def _get_polish_admin_group(self):
        group, _ = Group.objects.get_or_create(name=POLISH_ADMIN_GROUP_NAME)
        return group

    @admin.display(boolean=True, description="Polish admin")
    def is_polish_admin_member(self, obj):
        return obj.groups.filter(name=POLISH_ADMIN_GROUP_NAME).exists()

    @admin.action(description="Grant executive slides access")
    def grant_executive_slides_access(self, request, queryset):
        group = self._get_executive_group()
        updated = 0
        for user in queryset:
            user.groups.add(group)
            updated += 1
        self.message_user(request, f"Granted executive slides access to {updated} user(s).")

    @admin.action(description="Revoke executive slides access")
    def revoke_executive_slides_access(self, request, queryset):
        group = Group.objects.filter(name=self.executive_group_name).first()
        if not group:
            self.message_user(request, "No executive access group exists yet; nothing to revoke.")
            return

        updated = 0
        for user in queryset:
            user.groups.remove(group)
            updated += 1
        self.message_user(request, f"Revoked executive slides access from {updated} user(s).")

    @admin.action(description="Grant Polish admin access")
    def grant_polish_admin_access(self, request, queryset):
        group = self._get_polish_admin_group()
        updated = 0
        for user in queryset:
            user.groups.add(group)
            updated += 1
        self.message_user(request, f"Granted Polish admin access to {updated} user(s).")

    @admin.action(description="Revoke Polish admin access")
    def revoke_polish_admin_access(self, request, queryset):
        group = Group.objects.filter(name=POLISH_ADMIN_GROUP_NAME).first()
        if not group:
            self.message_user(request, "No Polish admin group exists yet; nothing to revoke.")
            return

        updated = 0
        for user in queryset:
            user.groups.remove(group)
            updated += 1
        self.message_user(request, f"Revoked Polish admin access from {updated} user(s).")


@admin.register(BillingWebhookEvent)
class BillingWebhookEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "provider",
        "event_type",
        "status",
        "signature_valid",
        "idempotency_key",
        "user",
        "target_tier",
        "processed_at",
        "created_at",
    )
    list_filter = ("provider", "status", "signature_valid")
    search_fields = ("idempotency_key", "provider_event_id", "event_type", "user__email", "error_message")


@admin.register(BillingCheckoutIntent)
class BillingCheckoutIntentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "provider",
        "user",
        "requested_tier",
        "status",
        "provider_session_id",
        "created_at",
        "updated_at",
    )
    list_filter = ("provider", "requested_tier", "status")
    search_fields = ("user__email", "idempotency_key", "provider_session_id", "error_message")