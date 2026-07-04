from django.conf import settings
from django.db import models
from rest_framework import permissions, serializers, viewsets


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OwnedModel(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_owned",
    )

    class Meta:
        abstract = True


class BasePermissions(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        owner_id = getattr(obj, "owner_id", None)
        if user and user.is_staff:
            return True
        if owner_id is None:
            return False
        return bool(user and user.is_authenticated and owner_id == user.id)


class BaseSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "owner")


class BaseView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, BasePermissions]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


# Backward-compatible aliases used by early adopters of this module.
TimestampedModel = BaseModel
OwnerOrStaffPermission = BasePermissions
BaseModelSerializer = BaseSerializer
OwnerScopedModelViewSet = BaseView
