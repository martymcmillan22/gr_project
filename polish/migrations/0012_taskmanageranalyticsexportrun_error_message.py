from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("polish", "0011_taskmanageranalyticsexportrun"),
    ]

    operations = [
        migrations.AddField(
            model_name="taskmanageranalyticsexportrun",
            name="error_message",
            field=models.TextField(blank=True),
        ),
    ]
