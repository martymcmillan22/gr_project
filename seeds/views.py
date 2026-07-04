from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from peringram.models import Industry

from .models import CrossReference, Idea
from .serializers import CrossReferenceSerializer, IdeaCaptureSerializer, IdeaSerializer
from .services import find_similar_ideas, validate_idea_submission


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
