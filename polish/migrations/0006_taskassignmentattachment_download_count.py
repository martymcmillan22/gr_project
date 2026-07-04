from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("polish", "0005_taskassignmentattachment"),
    ]

    operations = [
        migrations.AddField(
            model_name="taskassignmentattachment",
            name="download_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
