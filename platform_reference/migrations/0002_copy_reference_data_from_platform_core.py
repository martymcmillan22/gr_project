from django.db import migrations


def copy_reference_data(apps, schema_editor):
    OldGICS = apps.get_model("platform_core", "GICSReference")
    OldNAICS = apps.get_model("platform_core", "NAICSReference")
    NewGICSSchema = apps.get_model("platform_reference", "PlatformReferenceGICSReferenceSchema")
    NewNAICSSchema = apps.get_model("platform_reference", "PlatformReferenceNAICSReferenceSchema")

    for row in OldGICS.objects.order_by("id").iterator():
        NewGICSSchema.objects.update_or_create(
            id=row.id,
            defaults={
                "code": row.code,
                "name": row.name,
                "level": row.level,
                "parent_code": row.parent_code,
                "description": row.description,
                "source_version": row.source_version,
                "is_active": row.is_active,
                "updated_at": row.updated_at,
                "created_at": row.created_at,
            },
        )

    for row in OldNAICS.objects.order_by("id").iterator():
        NewNAICSSchema.objects.update_or_create(
            id=row.id,
            defaults={
                "code": row.code,
                "title": row.title,
                "description": row.description,
                "sector_code": row.sector_code,
                "source_version": row.source_version,
                "is_active": row.is_active,
                "updated_at": row.updated_at,
                "created_at": row.created_at,
            },
        )


def reverse_copy_reference_data(apps, schema_editor):
    NewGICSSchema = apps.get_model("platform_reference", "PlatformReferenceGICSReferenceSchema")
    NewNAICSSchema = apps.get_model("platform_reference", "PlatformReferenceNAICSReferenceSchema")

    # Safe only before runtime bridge models are flipped to platform_reference_* tables.
    # After cutover, do not reverse this migration without an explicit rollback plan.
    NewGICSSchema.objects.all().delete()
    NewNAICSSchema.objects.all().delete()


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("platform_reference", "0001_initial_reference_tables"),
        ("platform_core", "0019_rename_platform_co_level_3b70f8_idx_platform_co_level_60ea83_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_reference_data, reverse_copy_reference_data),
    ]