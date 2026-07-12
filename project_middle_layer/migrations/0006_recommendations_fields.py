from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project_middle_layer", "0005_semanticalert_snapshot_schema_issues"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectevolutionsnapshot",
            name="recommendations",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="semanticlineagerecord",
            name="recommendations",
            field=models.JSONField(default=list),
        ),
    ]
