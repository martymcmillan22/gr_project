from django.http import JsonResponse
from django.template.response import TemplateResponse

from .services import COMPARTMENTS
from .services import decode_color_code
from .services import encode_identity_and_display
from .services import encode_ontology_path
from .services import get_boundary_metadata
from .services import get_compartment_metadata
from .services import get_semantic_activation_payload
from .services import split_local_index


def _parse_int_param(request, key):
	value = request.GET.get(key)
	if value is None:
		return None
	try:
		return int(value)
	except (TypeError, ValueError):
		raise ValueError(f"Query parameter '{key}' must be an integer.")


def boundary_health_view(request):
	return JsonResponse(get_boundary_metadata())


def semantic_activation_view(request):
	return JsonResponse(get_semantic_activation_payload())


def semantic_subject_grid_view(request):
	catalog = [get_compartment_metadata(cid) for cid in sorted(COMPARTMENTS.keys())]
	return TemplateResponse(
		request,
		"platform_semantic/subject_grid.html",
		{
			"title": "Semantic Subject Grid",
			"catalog": catalog,
			"catalog_api": "/platform/semantic/color-preview/?catalog=1",
		},
	)


def semantic_color_preview_view(request):
	try:
		if request.GET.get("catalog") in {"1", "true", "True"}:
			catalog = [get_compartment_metadata(cid) for cid in sorted(COMPARTMENTS.keys())]
			return JsonResponse(
				{
					"mode": "catalog",
					"compartments": catalog,
					"swatch_asset": "docs/architecture/assets/semantic_anchor_bands.svg",
				}
			)

		color_code = _parse_int_param(request, "color_code")
		if color_code is not None:
			compartment_id, local_index = decode_color_code(color_code)
			payload = encode_identity_and_display(compartment_id=compartment_id, local_index=local_index)
			industry_index, subindustry_index, node_index = split_local_index(local_index)
			payload["path"] = {
				"industry_index": industry_index,
				"subindustry_index": subindustry_index,
				"node_index": node_index,
			}
			payload["mode"] = "color_code"
			return JsonResponse(payload)

		compartment_id = _parse_int_param(request, "compartment_id")
		local_index = _parse_int_param(request, "local_index")
		if compartment_id is not None and local_index is not None:
			payload = encode_identity_and_display(compartment_id=compartment_id, local_index=local_index)
			payload["mode"] = "node"
			return JsonResponse(payload)

		sector = request.GET.get("sector")
		subject = request.GET.get("subject")
		industry = request.GET.get("industry")
		subindustry = request.GET.get("subindustry")
		node_index = _parse_int_param(request, "node_index")
		if node_index is None:
			node_index = 0

		if sector and subject and industry and subindustry:
			payload = encode_ontology_path(
				sector=sector,
				subject=subject,
				industry=industry,
				subindustry=subindustry,
				node_index=node_index,
			)
			payload["mode"] = "ontology_path"
			return JsonResponse(payload)

		return JsonResponse(
			{
				"detail": (
					"Provide either color_code, compartment_id+local_index, or "
					"sector+subject+industry+subindustry (optional node_index)."
				),
				"compartment_example": get_compartment_metadata(0),
			},
			status=400,
		)
	except ValueError as exc:
		return JsonResponse({"detail": str(exc)}, status=400)

