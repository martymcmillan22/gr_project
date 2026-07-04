from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("polish", "0009_attachment_quarantine_and_audit_log"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="taskattachmentquarantine",
            name="review_notes",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="taskattachmentquarantine",
            name="review_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("approved", "Approved"),
                    ("rescanned", "Rescanned"),
                    ("deleted", "Deleted"),
                ],
                default="pending",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="taskattachmentquarantine",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="taskattachmentquarantine",
            name="reviewed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reviewed_task_quarantine_items",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
