from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project_middle_layer", "0011_semantic_intelligence_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="semanticanalyticssnapshot",
            name="branch_filter",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="semanticanalyticssnapshot",
            name="chart_series",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="semanticanalyticssnapshot",
            name="tier_filter",
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
