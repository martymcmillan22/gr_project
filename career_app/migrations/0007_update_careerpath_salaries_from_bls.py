from django.db import migrations


def apply_bls_updates(apps, schema_editor):
    CareerPath = apps.get_model("career_app", "CareerPath")

    updates = [
        {
            "subject": "Healthcare Administration",
            "degree_level_code": 2,
            "degree_name": "Bachelor Degree",
            "career_title": "Healthcare Administrator",
            "salary_metric": "$117,960",
        },
        {
            "subject": "Psychology",
            "degree_level_code": 3,
            "degree_name": "Master Degree",
            "career_title": "Marriage and Family Therapist",
            "salary_metric": "$63,780",
        },
        {
            "subject": "Marketing",
            "degree_level_code": 2,
            "degree_name": "Bachelor Degree",
            "career_title": "Marketing Specialist",
            "salary_metric": "$76,950",
        },
        {
            "subject": "Agricultural Science",
            "degree_level_code": 4,
            "degree_name": "Doctoral Degree",
            "career_title": "Agricultural Scientist",
            "salary_metric": "$78,770",
        },
    ]

    for row in updates:
        CareerPath.objects.update_or_create(
            subject=row["subject"],
            degree_level_code=row["degree_level_code"],
            degree_name=row["degree_name"],
            career_title=row["career_title"],
            defaults={"salary_metric": row["salary_metric"]},
        )


def rollback_bls_updates(apps, schema_editor):
    CareerPath = apps.get_model("career_app", "CareerPath")

    previous_values = [
        {
            "subject": "Healthcare Administration",
            "degree_level_code": 2,
            "degree_name": "Bachelor Degree",
            "career_title": "Healthcare Administrator",
            "salary_metric": "$110,680",
        },
        {
            "subject": "Agricultural Science",
            "degree_level_code": 4,
            "degree_name": "Doctoral Degree",
            "career_title": "Agricultural Scientist",
            "salary_metric": "$91,100",
        },
    ]

    for row in previous_values:
        CareerPath.objects.update_or_create(
            subject=row["subject"],
            degree_level_code=row["degree_level_code"],
            degree_name=row["degree_name"],
            career_title=row["career_title"],
            defaults={"salary_metric": row["salary_metric"]},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("career_app", "0006_prepopulate_more_careerpaths"),
    ]

    operations = [
        migrations.RunPython(apply_bls_updates, rollback_bls_updates),
    ]
