from django.http import JsonResponse

from .services import get_boundary_metadata
from .services import get_quadrant_activation_payload


def boundary_health_view(request):
	return JsonResponse(get_boundary_metadata())


def quadrant_activation_view(request):
	return JsonResponse(get_quadrant_activation_payload())

