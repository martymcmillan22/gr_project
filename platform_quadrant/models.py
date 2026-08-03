"""Platform quadrant boundary model aliases.

Phase-4 activation keeps data ownership unchanged and exposes deterministic
read aliases for quadrant services.
"""

from platform_core.models import MLASClassificationRecord
from platform_core.models import SemanticBundle
from platform_core.models import SemanticBundleRevision
from platform_core.models import SemanticPreset
from platform_core.models import Slide
from platform_reference.models import PlatformReferenceGICSReferenceSchema
from platform_reference.models import PlatformReferenceNAICSReferenceSchema

GICSReference = PlatformReferenceGICSReferenceSchema
NAICSReference = PlatformReferenceNAICSReferenceSchema

__all__ = [
	"GICSReference",
	"MLASClassificationRecord",
	"NAICSReference",
	"SemanticBundle",
	"SemanticBundleRevision",
	"SemanticPreset",
	"Slide",
]
