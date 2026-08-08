from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("homepage_backend", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepagepreference",
            name="view_state",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
