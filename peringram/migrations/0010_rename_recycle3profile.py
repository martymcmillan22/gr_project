from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("peringram", "0009_seed_latticecompartment_registry"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="RecycleThreeAllocation",
            new_name="Recycle3Profile",
        ),
        migrations.RenameField(
            model_name="recycle3profile",
            old_name="corporation_rd",
            new_name="corporation_rnd_pct",
        ),
        migrations.RenameField(
            model_name="recycle3profile",
            old_name="people_small_business_qcqa",
            new_name="people_qcqa_pct",
        ),
        migrations.RenameField(
            model_name="recycle3profile",
            old_name="government_infrastructure_protection",
            new_name="government_infra_pct",
        ),
        migrations.RenameField(
            model_name="recycle3profile",
            old_name="isea_gdp_optimization",
            new_name="isea_pct",
        ),
    ]
