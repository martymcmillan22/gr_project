from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from peringram.models import Industry
from peringram.pip_state import PIPState
from peringram.rr import RRAccessDeniedError, RRService
from peringram.srl import SRLService
from peringram.views import seed_peringram_structure
from peringram.models import Recycle3Profile

from .models import Business, CrossReference, Idea, Seed
from .serializers import (
	CrossReferenceSerializer,
	BusinessSerializer,
	IdeaCaptureSerializer,
	IdeaSerializer,
	ProjectActivationSerializer,
	SeedPromotionSerializer,
	SeedSerializer,
)
from .rr_visual_system import build_operating_stack_payload
from .rr_visual_system import build_rr_card_spec_payload
from .rr_visual_system import build_rr_dashboard_payload
from .rr_visual_system import build_rr_industry_map_payload
from .rr_visual_system import build_rr_node_detail_payload
from .rr_visual_system import build_semantic_action_engine_payload
from .rr_visual_system import build_semantic_intelligence_payload
from .rr_visual_system import build_va_guidance_payload
from .rr_visual_system import execute_semantic_action
from .services import find_similar_ideas, validate_idea_submission


ISPE_INDUSTRY_ALIASES = {
	"media / publishing": "Language - Foundation",
	"media publishing": "Language - Foundation",
	"newsletter": "Language - Foundation",
	"editorial": "Language - Foundation",
	"editorial identity": "Language - Foundation",
}


def _resolve_canonical_industry(industry_label):
	seed_peringram_structure()
	normalized_label = " ".join((industry_label or "").split()).strip()
	if not normalized_label:
		raise ValueError("Industry label is required.")
	target_name = ISPE_INDUSTRY_ALIASES.get(normalized_label.casefold(), normalized_label)
	industry = Industry.objects.select_related("group").filter(name__iexact=target_name).first()
	if industry is not None:
		return industry
	raise ValueError(
		f"Unknown industry '{industry_label}'. Use a canonical Peringram industry name or a supported ISPE alias."
	)


def _build_raw_content(payload):
	parts = [
		f"Purpose: {payload['purpose']}",
		f"Audience: {payload.get('audience') or 'unspecified'}",
		f"Narrative: {payload.get('narrative') or 'unspecified'}",
		f"Notes: {payload.get('notes') or 'none'}",
	]
	return "\n".join(parts)


def _build_project_notes(payload, activation_snapshot):
	project_notes = payload.get("project_notes", {}) or {}
	project_notes.setdefault("phase", "project")
	project_notes.setdefault("metadata", payload.get("metadata", {}) or {})
	project_notes.setdefault("activation_snapshot", activation_snapshot)
	return project_notes


def _build_project_activation_snapshot(pip_state, request):
	return {
		"mode": request.query_params.get("mode", "assistive"),
		"include_va": request.query_params.get("include_va", "1") in {"1", "true", "True"},
		"final_tier": pip_state.final_tier,
		"lifecycle_stage": pip_state.lifecycle_stage,
		"territory_index": pip_state.territory.index if pip_state.territory is not None else None,
		"time_slot_time_frame": pip_state.time_slot_time_frame,
		"rr_allowed_now": pip_state.rr_allowed_now,
	}


def _build_pip_state_for_user(user):
	recycle, _ = Recycle3Profile.objects.get_or_create(user=user)
	territory = SRLService.assign_compartment(user)
	return PIPState.from_recycle3(recycle, territory=territory)


class CrossReferenceReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
	serializer_class = CrossReferenceSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		queryset = CrossReference.objects.select_related(
			"source_business__seed__idea__industry",
			"target_business__seed__idea__industry",
		)

		relationship_type = self.request.query_params.get("relationship_type")
		source_industry_id = self.request.query_params.get("source_industry_id")
		target_industry_id = self.request.query_params.get("target_industry_id")
		min_score = self.request.query_params.get("min_score")

		if relationship_type:
			queryset = queryset.filter(relationship_type=relationship_type)
		if source_industry_id:
			queryset = queryset.filter(source_business__seed__idea__industry_id=source_industry_id)
		if target_industry_id:
			queryset = queryset.filter(target_business__seed__idea__industry_id=target_industry_id)
		if min_score:
			try:
				queryset = queryset.filter(score__gte=float(min_score))
			except ValueError:
				pass

		return queryset


class IdeaCaptureAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		serializer = IdeaCaptureSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		payload = serializer.validated_data

		industry = Industry.objects.get(id=payload["industry_id"])
		raw_content = payload["raw_content"]
		compartment_id = payload.get("compartment_id")
		metadata = payload.get("metadata") or {}

		lattice_validation = None
		if compartment_id is not None:
			lattice_validation = validate_idea_submission(compartment_id, raw_content, metadata=metadata)
			if lattice_validation["status"] != "approved":
				return Response(
					{"detail": "Lattice validation failed.", "lattice_validation": lattice_validation},
					status=status.HTTP_400_BAD_REQUEST,
				)

		idea = Idea.objects.create(
			user=request.user,
			industry=industry,
			raw_content=raw_content,
			status=Idea.STATUS_RAW,
		)
		candidates = find_similar_ideas(raw_content, industry_id=industry.id, exclude_idea_id=idea.id)

		return Response(
			{
				"idea": IdeaSerializer(idea).data,
				"cross_reference_candidate_ids": candidates,
				"lattice_validation": lattice_validation,
			},
			status=status.HTTP_201_CREATED,
		)


class SeedPromotionAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		serializer = SeedPromotionSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		payload = serializer.validated_data

		try:
			industry = _resolve_canonical_industry(payload["industry"])
		except ValueError as error:
			return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)

		promotion_context = {
			"source": "ispe",
			"phase": "seed",
			"purpose": payload["purpose"],
			"industry": payload["industry"],
			"audience": payload.get("audience", ""),
			"narrative": payload.get("narrative", ""),
			"notes": payload.get("notes", ""),
			"identity": {
				"name": payload["identity_name"],
				"type": payload["identity_type"],
				"purpose": payload.get("identity_purpose", ""),
				"structure": payload.get("identity_structure", ""),
			},
			"deliverables": {
				"summary": payload.get("deliverables", ""),
				"structure": payload.get("deliverable_structure", ""),
				"cadence": payload.get("deliverable_cadence", ""),
			},
			"workflow": {
				"next_phase": "project",
				"project_ready": True,
			},
			"metadata": payload.get("metadata", {}),
		}

		raw_content = _build_raw_content(payload)
		with transaction.atomic():
			idea = Idea(
				user=request.user,
				industry=industry,
				raw_content=raw_content,
				status=Idea.STATUS_SEED,
			)
			idea._seed_promotion_payload = promotion_context
			idea.save()
			seed = idea.seed

		return Response(
			{
				"idea": IdeaSerializer(idea).data,
				"seed": SeedSerializer(seed).data,
				"project_ready": True,
				"next_phase": "project",
				"orchestration_hint": {
					"mode": "assistive",
					"surface": "/platform/orchestration/",
					"query": "mode=assistive&include_va=1",
				},
			},
			status=status.HTTP_201_CREATED,
		)


class ProjectActivationAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		serializer = ProjectActivationSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		payload = serializer.validated_data

		seed = Seed.objects.select_related("idea__industry", "idea__user").filter(
			pk=payload["seed_id"],
			idea__user=request.user,
		).first()
		if seed is None:
			return Response({"detail": "Seed not found for the current user."}, status=status.HTTP_404_NOT_FOUND)

		pip_state = _build_pip_state_for_user(request.user)
		project_notes = _build_project_notes(payload, _build_project_activation_snapshot(pip_state, request))

		try:
			with transaction.atomic():
				business = RRService.promote_seed_to_project(
					pip_state,
					seed,
					brand_name=payload["project_name"],
					market_status=payload.get("market_status", "draft"),
					metadata=payload.get("metadata", {}),
					project_notes=project_notes,
				)
		except RRAccessDeniedError as error:
			return Response(
				{
					"detail": str(error),
					"project_ready": False,
					"next_phase": "project",
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		return Response(
			{
				"business": BusinessSerializer(business).data,
				"project_ready": True,
				"next_phase": "project",
				"activation_hint": {
					"surface": "/platform/activation/",
					"mode": "assistive",
				},
				"orchestration_hint": {
					"surface": "/platform/orchestration/",
					"query": "mode=assistive&include_va=1",
				},
			},
			status=status.HTTP_201_CREATED,
		)


class RRDashboardAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		phase_filter = (request.query_params.get("phase") or "").strip()
		limit = request.query_params.get("limit")
		try:
			limit_value = int(limit) if limit is not None else 10
		except ValueError:
			return Response({"detail": "limit must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
		payload = build_rr_dashboard_payload(user=request.user, phase_filter=phase_filter, limit_per_lane=max(limit_value, 0))
		return Response(payload, status=status.HTTP_200_OK)


class RRIndustryMapAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		phase_filter = (request.query_params.get("phase") or "").strip()
		payload = build_rr_industry_map_payload(user=request.user, phase_filter=phase_filter)
		return Response(payload, status=status.HTTP_200_OK)


class RRCardSpecAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		compartment_id = request.query_params.get("compartment_id")
		if compartment_id is None:
			payload = build_rr_card_spec_payload()
			return Response(payload, status=status.HTTP_200_OK)

		try:
			parsed = int(compartment_id)
		except ValueError:
			return Response({"detail": "compartment_id must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

		try:
			payload = build_rr_card_spec_payload(compartment_id=parsed)
		except ValueError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
		return Response(payload, status=status.HTTP_200_OK)


class RRVAGuidanceAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		payload = build_va_guidance_payload(user=request.user)
		return Response(payload, status=status.HTTP_200_OK)


class RROperatingStackAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		payload = build_operating_stack_payload()
		return Response(payload, status=status.HTTP_200_OK)


class RRNodeDetailAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request, business_id):
		try:
			payload = build_rr_node_detail_payload(business_id=int(business_id), user=request.user)
		except ValueError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
		return Response(payload, status=status.HTTP_200_OK)


class RRSemanticIntelligenceAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		payload = build_semantic_intelligence_payload(user=request.user)
		return Response(payload, status=status.HTTP_200_OK)


class RRSemanticActionEngineAPIView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		payload = build_semantic_action_engine_payload(user=request.user)
		return Response(payload, status=status.HTTP_200_OK)

	def post(self, request):
		payload = request.data if isinstance(request.data, dict) else {}
		result = execute_semantic_action(payload=payload, user=request.user)
		result_status = str(result.get("status") or "")
		if result_status == "executed":
			return Response(result, status=status.HTTP_200_OK)
		if result_status == "blocked":
			return Response(result, status=status.HTTP_409_CONFLICT)
		if result_status == "failed":
			return Response(result, status=status.HTTP_409_CONFLICT)
		if result_status == "rejected":
			return Response(result, status=status.HTTP_400_BAD_REQUEST)
		return Response(result, status=status.HTTP_400_BAD_REQUEST)
