from django.db import migrations, models


def migrate_twist_statuses_forward(apps, schema_editor):
    CreativeIdea = apps.get_model("twist", "CreativeIdea")
    status_map = {
        "raw": "RAW",
        "developed": "SEED",
        "archived": "BUSINESS",
    }
    for old_status, new_status in status_map.items():
        CreativeIdea.objects.filter(status=old_status).update(status=new_status)


def migrate_twist_statuses_backward(apps, schema_editor):
    CreativeIdea = apps.get_model("twist", "CreativeIdea")
    status_map = {
        "RAW": "raw",
        "SEED": "developed",
        "BUSINESS": "archived",
    }
    for old_status, new_status in status_map.items():
        CreativeIdea.objects.filter(status=old_status).update(status=new_status)


class Migration(migrations.Migration):

    dependencies = [
        ("twist", "0003_creativeidea_status"),
    ]

    operations = [
        migrations.RunPython(migrate_twist_statuses_forward, migrate_twist_statuses_backward),
        migrations.AlterField(
            model_name="creativeidea",
            name="status",
            field=models.CharField(
                choices=[("RAW", "Raw"), ("SEED", "Seed"), ("BUSINESS", "Business")],
                default="RAW",
                max_length=20,
            ),
        ),
    ]
