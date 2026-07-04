from django.db import migrations


LATTICE_ROWS = [
    (1, "Red", "past", 4, "Math"),
    (2, "Blue", "present_past", 16, "Language"),
    (3, "Yellow", "present_future", 64, "Arts"),
    (4, "Green", "future", 256, "Science"),
    (5, "Purple", "past", 1024, "General Information"),
    (6, "Teal", "present_past", 4096, "Literature"),
    (7, "Orange", "present_future", 16384, "Crafts"),
    (8, "Lime", "future", 65536, "Technology"),
    (9, "Pink", "past", 262144, "History"),
    (10, "Cyan", "present_past", 1048576, "Geology"),
    (11, "Amber", "present_future", 4194304, "Philosophy/Ethics"),
    (12, "Green-Lime", "future", 16777216, "Systems/Synthesis"),
]


def seed_lattice_registry(apps, schema_editor):
    LatticeCompartment = apps.get_model("peringram", "LatticeCompartment")

    for index, color, time_frame, capacity, category in LATTICE_ROWS:
        LatticeCompartment.objects.update_or_create(
            index=index,
            defaults={
                "color": color,
                "time_frame": time_frame,
                "capacity": capacity,
                "category": category,
                "notes": "Base 4^n lattice registry record.",
            },
        )


def unseed_lattice_registry(apps, schema_editor):
    LatticeCompartment = apps.get_model("peringram", "LatticeCompartment")
    LatticeCompartment.objects.filter(index__gte=1, index__lte=12).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("peringram", "0008_latticecompartment"),
    ]

    operations = [
        migrations.RunPython(seed_lattice_registry, unseed_lattice_registry),
    ]
