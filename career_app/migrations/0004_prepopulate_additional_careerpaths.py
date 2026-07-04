from django.db import migrations


def seed_additional_career_paths(apps, schema_editor):
    CareerPath = apps.get_model("career_app", "CareerPath")

    rows = [
        # Engineering & Technology
        {
            "subject": "Engineering & Technology",
            "degree_level_code": 1,
            "degree_name": "Associate Degree",
            "career_title": "Drafter",
            "salary_metric": "$65,380",
        },
        {
            "subject": "Engineering & Technology",
            "degree_level_code": 2,
            "degree_name": "Bachelor Degree",
            "career_title": "Mechanical Engineer",
            "salary_metric": "$102,320",
        },
        {
            "subject": "Engineering & Technology",
            "degree_level_code": 3,
            "degree_name": "Master Degree",
            "career_title": "Civil Engineer",
            "salary_metric": "$99,590",
        },
        {
            "subject": "Engineering & Technology",
            "degree_level_code": 4,
            "degree_name": "Doctoral Degree",
            "career_title": "Architectural and Engineering Manager",
            "salary_metric": "$167,740",
        },
        # Education
        {
            "subject": "Education",
            "degree_level_code": 1,
            "degree_name": "Associate Degree",
            "career_title": "Preschool Teacher",
            "salary_metric": "$37,120",
        },
        {
            "subject": "Education",
            "degree_level_code": 2,
            "degree_name": "Bachelor Degree",
            "career_title": "High School Teacher",
            "salary_metric": "$64,580",
        },
        {
            "subject": "Education",
            "degree_level_code": 3,
            "degree_name": "Master Degree",
            "career_title": "Instructional Coordinator",
            "salary_metric": "$74,720",
        },
        {
            "subject": "Education",
            "degree_level_code": 4,
            "degree_name": "Doctoral Degree",
            "career_title": "Postsecondary Teacher",
            "salary_metric": "$83,980",
        },
        # Environmental Science
        {
            "subject": "Environmental Science",
            "degree_level_code": 1,
            "degree_name": "Associate Degree",
            "career_title": "Environmental Science and Protection Technician",
            "salary_metric": "$49,490",
        },
        {
            "subject": "Environmental Science",
            "degree_level_code": 2,
            "degree_name": "Bachelor Degree",
            "career_title": "Environmental Scientist and Specialist",
            "salary_metric": "$80,060",
        },
        {
            "subject": "Environmental Science",
            "degree_level_code": 3,
            "degree_name": "Master Degree",
            "career_title": "Hydrologist",
            "salary_metric": "$92,060",
        },
        {
            "subject": "Environmental Science",
            "degree_level_code": 4,
            "degree_name": "Doctoral Degree",
            "career_title": "Environmental Science Professor",
            "salary_metric": "$83,980",
        },
        # Finance & Accounting
        {
            "subject": "Finance & Accounting",
            "degree_level_code": 1,
            "degree_name": "Associate Degree",
            "career_title": "Bookkeeping, Accounting, and Auditing Clerk",
            "salary_metric": "$49,210",
        },
        {
            "subject": "Finance & Accounting",
            "degree_level_code": 2,
            "degree_name": "Bachelor Degree",
            "career_title": "Accountant and Auditor",
            "salary_metric": "$81,680",
        },
        {
            "subject": "Finance & Accounting",
            "degree_level_code": 3,
            "degree_name": "Master Degree",
            "career_title": "Financial Analyst",
            "salary_metric": "$101,910",
        },
        {
            "subject": "Finance & Accounting",
            "degree_level_code": 4,
            "degree_name": "Doctoral Degree",
            "career_title": "Personal Financial Advisor",
            "salary_metric": "$102,140",
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


def rollback_seed_additional_career_paths(apps, schema_editor):
    CareerPath = apps.get_model("career_app", "CareerPath")
    subjects = [
        "Engineering & Technology",
        "Education",
        "Environmental Science",
        "Finance & Accounting",
    ]
    CareerPath.objects.filter(subject__in=subjects).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("career_app", "0003_alter_careerpath_options_careerpath_salary_metric"),
    ]

    operations = [
        migrations.RunPython(
            seed_additional_career_paths,
            rollback_seed_additional_career_paths,
        ),
    ]
