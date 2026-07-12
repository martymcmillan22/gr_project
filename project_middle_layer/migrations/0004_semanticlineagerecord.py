from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("project_middle_layer", "0003_projectevolutionsnapshot_confidence"),
    ]

    operations = [
        migrations.CreateModel(
            name="SemanticLineageRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("lineage_tree", models.JSONField(default=dict)),
                ("semantic_clusters", models.JSONField(default=list)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lineage_records",
                        to="project_middle_layer.projectnode",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
