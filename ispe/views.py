from django.http import JsonResponse

from .services import build_ispe_activation_payload


def ispe_activation_view(request):
    mode = request.GET.get("mode")
    phase = request.GET.get("phase")
    include_va_value = str(request.GET.get("include_va", "1")).strip().lower()
    include_va = include_va_value in {"1", "true", "yes", "y", "on"}

    return JsonResponse(
        build_ispe_activation_payload(
            mode=str(mode or ""),
            include_va=include_va,
            phase=str(phase or ""),
        )
    )
