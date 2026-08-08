from django.db import models

from platform_core.backend import BaseModel, OwnedModel


class HomepageBackendItem(OwnedModel, BaseModel):
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-updated_at"]
        permissions = [
            ("view_homepage_backend_item_analytics", "Can view HomepageBackendItem analytics"),
        ]

    def __str__(self):
        return self.title


class HomepageTask(OwnedModel, BaseModel):
    STATUS_TODO = "todo"
    STATUS_DOING = "doing"
    STATUS_DONE = "done"
    STATUS_CHOICES = [
        (STATUS_TODO, "To Do"),
        (STATUS_DOING, "Doing"),
        (STATUS_DONE, "Done"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_TODO)

    class Meta:
        ordering = ["status", "-updated_at"]

    def __str__(self):
        return self.title


class HomepageFlow(OwnedModel, BaseModel):
    STATUS_ACTIVE = "active"
    STATUS_BLOCKED = "blocked"
    STATUS_COMPLETE = "complete"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_BLOCKED, "Blocked"),
        (STATUS_COMPLETE, "Complete"),
    ]

    name = models.CharField(max_length=160)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    progress = models.PositiveSmallIntegerField(default=0)
    message = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


class HomepagePreference(OwnedModel, BaseModel):
    notifications = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=False)
    view_state = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Preferences for {self.owner_id}"


class HomepageAction(OwnedModel, BaseModel):
    label = models.CharField(max_length=120)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.label
