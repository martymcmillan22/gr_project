from platform_reference.services.reference_sync import (  # Compatibility shim during split.
    get_gics_source_status,
    is_demo_gics_source,
    is_production_environment,
)

__all__ = [
    "get_gics_source_status",
    "is_demo_gics_source",
    "is_production_environment",
]
