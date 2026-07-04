from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="subscription_tier",
            field=models.CharField(
                choices=[
                    ("free", "Free"),
                    ("premium_starter", "Premium Starter"),
                    ("premium_pro", "Premium Pro"),
                    ("premium_enterprise", "Premium Enterprise"),
                ],
                default="free",
                max_length=32,
            ),
        ),
    ]
