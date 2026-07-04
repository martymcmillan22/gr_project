from django.db import migrations


def seed_more_career_paths(apps, schema_editor):
    CareerPath = apps.get_model("career_app", "CareerPath")

    rows = [
        {
            "subject": "Healthcare Administration",
            "degree_level_code": 2,
            "degree_name": "Bachelor Degree",
            "career_title": "Healthcare Administrator",
            "salary_metric": "$110,680",
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
            "salary_metric": "$91,100",
        },
    ]

    for row in rows:
        CareerPath.objects.get_or_create(
            subject=row["subject"],
            degree_level_code=row["degree_level_code"],
            degree_name=row["degree_name"],
            career_title=row["career_title"],
            defaults={"salary_metric": row["salary_metric"]},
        )


def rollback_seed_more_career_paths(apps, schema_editor):
    CareerPath = apps.get_model("career_app", "CareerPath")
    rows = [
        ("Healthcare Administration", 2, "Bachelor Degree", "Healthcare Administrator"),
        ("Psychology", 3, "Master Degree", "Marriage and Family Therapist"),
        ("Marketing", 2, "Bachelor Degree", "Marketing Specialist"),
        ("Agricultural Science", 4, "Doctoral Degree", "Agricultural Scientist"),
    ]

    for subject, degree_level_code, degree_name, career_title in rows:
        CareerPath.objects.filter(
            subject=subject,
            degree_level_code=degree_level_code,
            degree_name=degree_name,
            career_title=career_title,
        ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("career_app", "0005_careerfilterpreset"),
    ]

    operations = [
        migrations.RunPython(seed_more_career_paths, rollback_seed_more_career_paths),
    ]
