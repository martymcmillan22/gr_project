"""Platform semantic boundary model aliases.

This phase activates the semantic boundary as a read-layer over canonical
models that are currently owned by platform_core and platform_reference.
No schema ownership changes are introduced in this step.
"""

from platform_core.models import MLASClassificationRecord
from platform_core.models import SemanticBundle
from platform_core.models import SemanticBundleRevision
from platform_core.models import SemanticBundleRevisionTag
from platform_core.models import SemanticPreset
from platform_core.models import Slide
from platform_reference.models import PlatformReferenceGICSReferenceSchema
from platform_reference.models import PlatformReferenceNAICSReferenceSchema

# Canonical reference aliases used by semantic services.
GICSReference = PlatformReferenceGICSReferenceSchema
NAICSReference = PlatformReferenceNAICSReferenceSchema

__all__ = [
	"GICSReference",
	"MLASClassificationRecord",
	"NAICSReference",
	"SemanticBundle",
	"SemanticBundleRevision",
	"SemanticBundleRevisionTag",
	"SemanticPreset",
	"Slide",
]
