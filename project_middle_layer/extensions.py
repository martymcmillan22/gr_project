from __future__ import annotations

from django.utils import timezone

from project_middle_layer.models import SemanticExtension


def validate_extension_patch(*, schema_patch: dict[str, object], rules_patch: dict[str, object]) -> dict[str, object]:
    schema_valid = isinstance(schema_patch, dict)
    rules_valid = isinstance(rules_patch, dict)
    return {
        "valid": schema_valid and rules_valid,
        "schema_valid": schema_valid,
        "rules_valid": rules_valid,
        "message": "ok" if (schema_valid and rules_valid) else "schema_patch and rules_patch must be JSON objects",
    }


def apply_semantic_extension(*, extension_slug: str) -> dict[str, object]:
    extension = SemanticExtension.objects.filter(slug=extension_slug).first()
    if not extension:
        raise ValueError("Semantic extension not found.")

    report = validate_extension_patch(
        schema_patch=extension.schema_patch,
        rules_patch=extension.rules_patch,
    )
    extension.validation_report = report
    if not report["valid"]:
        extension.save(update_fields=["validation_report", "updated_at"])
        raise ValueError(report["message"])

    extension.rollback_payload = {
        "schema_patch": extension.schema_patch,
        "rules_patch": extension.rules_patch,
        "applied_at": timezone.now().isoformat(),
    }
    extension.is_applied = True
    extension.applied_at = timezone.now()
    extension.save(update_fields=["validation_report", "rollback_payload", "is_applied", "applied_at", "updated_at"])

    return {
        "extension_slug": extension.slug,
        "status": "applied",
        "validation_report": extension.validation_report,
    }


def rollback_semantic_extension(*, extension_slug: str) -> dict[str, object]:
    extension = SemanticExtension.objects.filter(slug=extension_slug).first()
    if not extension:
        raise ValueError("Semantic extension not found.")

    extension.is_applied = False
    extension.applied_at = None
    extension.save(update_fields=["is_applied", "applied_at", "updated_at"])

    return {
        "extension_slug": extension.slug,
        "status": "rolled_back",
        "rollback_payload": extension.rollback_payload,
    }
