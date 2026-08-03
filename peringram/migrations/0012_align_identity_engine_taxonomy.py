from django.db import migrations


LATTICE_CATEGORY_BY_INDEX = {
    1: "Math",
    2: "Language",
    3: "Arts",
    4: "Science",
    5: "General Information",
    6: "Literature",
    7: "Crafts",
    8: "Technology",
    9: "History",
    10: "Geography",
    11: "Architecture",
    12: "Ecology",
}

GROUP_NAME_BY_CODE = {
    1: "Math",
    2: "Language",
    3: "Arts",
    4: "Science",
    5: "General Information",
    6: "Literature",
    7: "Crafts",
    8: "Technology",
    9: "History",
    10: "Geography",
    11: "Architecture",
    12: "Ecology",
    13: "Philosophy",
    14: "Law and Governance",
    15: "Economics",
    16: "Systemics",
}


def apply_identity_engine_taxonomy(apps, schema_editor):
    LatticeCompartment = apps.get_model("peringram", "LatticeCompartment")
    IndustryGroup = apps.get_model("peringram", "IndustryGroup")

    for index, category in LATTICE_CATEGORY_BY_INDEX.items():
        LatticeCompartment.objects.filter(index=index).update(category=category)

    for code, name in GROUP_NAME_BY_CODE.items():
        IndustryGroup.objects.filter(code=code).update(
            name=name,
            description=f"Domain group {code}: {name}.",
        )


def rollback_identity_engine_taxonomy(apps, schema_editor):
    # No destructive rollback. Keep newer canonical taxonomy in place.
    return


class Migration(migrations.Migration):

    dependencies = [
        ("peringram", "0011_userlatticeassignment"),
    ]

    operations = [
        migrations.RunPython(apply_identity_engine_taxonomy, rollback_identity_engine_taxonomy),
    ]
