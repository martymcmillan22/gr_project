from django.http import JsonResponse

from .services import get_boundary_metadata
from .services import get_semantic_activation_payload


def boundary_health_view(request):
	return JsonResponse(get_boundary_metadata())


def semantic_activation_view(request):
	return JsonResponse(get_semantic_activation_payload())

