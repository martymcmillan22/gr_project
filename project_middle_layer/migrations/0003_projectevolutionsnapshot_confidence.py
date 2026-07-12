from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project_middle_layer", "0002_projectevolutionsnapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectevolutionsnapshot",
            name="confidence_label",
            field=models.CharField(default="Volatile", max_length=20),
        ),
        migrations.AddField(
            model_name="projectevolutionsnapshot",
            name="confidence_score",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
