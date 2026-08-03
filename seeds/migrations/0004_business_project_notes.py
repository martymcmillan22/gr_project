from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		("seeds", "0003_cross_reference_and_lifecycle_indexes"),
	]

	operations = [
		migrations.AddField(
			model_name="business",
			name="project_notes",
			field=models.JSONField(blank=True, default=dict),
		),
	]