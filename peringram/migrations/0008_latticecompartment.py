import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("peringram", "0007_alter_industrygroup_code"),
    ]

    operations = [
        migrations.CreateModel(
            name="LatticeCompartment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "index",
                    models.PositiveSmallIntegerField(
                        help_text="Lattice compartment number 1-12.",
                        unique=True,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(12),
                        ],
                    ),
                ),
                ("color", models.CharField(max_length=20)),
                (
                    "time_frame",
                    models.CharField(
                        choices=[
                            ("past", "Past"),
                            ("present_past", "Present/Past"),
                            ("present_future", "Present/Future"),
                            ("future", "Future"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "capacity",
                    models.BigIntegerField(help_text="Geometric series capacity based on 4^index."),
                ),
                ("category", models.CharField(max_length=80)),
                ("notes", models.TextField(blank=True)),
            ],
            options={"ordering": ["index"]},
        ),
    ]
