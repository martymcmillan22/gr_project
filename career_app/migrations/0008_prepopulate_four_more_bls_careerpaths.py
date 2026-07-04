from django.db import migrations


def seed_four_more_bls_career_paths(apps, schema_editor):
    CareerPath = apps.get_model("career_app", "CareerPath")

    rows = [
        {
            "subject": "Cybersecurity",
            "degree_level_code": 2,
            "degree_name": "Bachelor Degree",
            "career_title": "Information Security Analyst",
            "salary_metric": "$124,910",
        },
        {
            "subject": "Supply Chain & Logistics",
            "degree_level_code": 2,
            "degree_name": "Bachelor Degree",
            "career_title": "Logistician",
            "salary_metric": "$80,880",
        },
        {
            "subject": "Public Health",
            "degree_level_code": 3,
            "degree_name": "Master Degree",
            "career_title": "Epidemiologist",
            "salary_metric": "$83,980",
        },
        {
            "subject": "Environmental Engineering",
            "degree_level_code": 2,
            "degree_name": "Bachelor Degree",
            "career_title": "Environmental Engineer",
            "salary_metric": "$104,170",
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


def rollback_seed_four_more_bls_career_paths(apps, schema_editor):
    CareerPath = apps.get_model("career_app", "CareerPath")

    rows = [
        ("Cybersecurity", 2, "Bachelor Degree", "Information Security Analyst"),
        ("Supply Chain & Logistics", 2, "Bachelor Degree", "Logistician"),
        ("Public Health", 3, "Master Degree", "Epidemiologist"),
        ("Environmental Engineering", 2, "Bachelor Degree", "Environmental Engineer"),
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
        ("career_app", "0007_update_careerpath_salaries_from_bls"),
    ]

    operations = [
        migrations.RunPython(
            seed_four_more_bls_career_paths,
            rollback_seed_four_more_bls_career_paths,
        ),
    ]
