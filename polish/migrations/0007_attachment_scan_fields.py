from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("polish", "0006_taskassignmentattachment_download_count"),
    ]

    operations = [
        migrations.AddField(
            model_name="taskassignmentattachment",
            name="file_sha256",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="taskassignmentattachment",
            name="scan_notes",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="taskassignmentattachment",
            name="scan_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("clean", "Clean"),
                    ("flagged", "Flagged"),
                    ("error", "Error"),
                ],
                default="pending",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="taskassignmentattachment",
            name="scanned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
