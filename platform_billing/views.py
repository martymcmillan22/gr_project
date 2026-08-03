from django.http import JsonResponse

from .services import get_boundary_metadata


def boundary_health_view(request):
	return JsonResponse(get_boundary_metadata())

