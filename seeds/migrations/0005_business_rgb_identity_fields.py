from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seeds", "0004_business_project_notes"),
    ]

    operations = [
        migrations.AddField(
            model_name="business",
            name="color_code",
            field=models.PositiveIntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="business",
            name="compartment_id",
            field=models.PositiveSmallIntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="business",
            name="display_rgb",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
