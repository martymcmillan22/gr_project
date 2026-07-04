from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("polish", "0007_attachment_scan_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="taskassignment",
            name="completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="taskassignment",
            name="completion_notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="taskassignmentattachment",
            name="file_size_bytes",
            field=models.BigIntegerField(default=0),
        ),
    ]
