import csv

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from ontology.models import Branch, Industry, Subject, SubIndustry, TemporalSlot
from ontology.serializers import (
	BranchSerializer,
	IndustrySerializer,
	SubjectSerializer,
	SubIndustrySerializer,
	TemporalSlotSerializer,
)
from ontology.services.linear_generator import generate_linear_hierarchy
from ontology.services.lattice import build_lattice_nodes


class SubjectViewSet(viewsets.ModelViewSet):
	queryset = Subject.objects.all().order_by("order")
	serializer_class = SubjectSerializer
	permission_classes = [IsAuthenticatedOrReadOnly]

	def get_queryset(self):
		queryset = super().get_queryset()
		name = self.request.query_params.get("name")
		acronym = self.request.query_params.get("acronym")

		if name:
			queryset = queryset.filter(name__iexact=name)
		if acronym:
			queryset = queryset.filter(acronym__iexact=acronym)
		return queryset


class BranchViewSet(viewsets.ModelViewSet):
	queryset = Branch.objects.select_related("subject").all().order_by("subject__order", "order")
	serializer_class = BranchSerializer
	permission_classes = [IsAuthenticatedOrReadOnly]

	def get_queryset(self):
		queryset = super().get_queryset()
		subject = self.request.query_params.get("subject")
		subject_id = self.request.query_params.get("subject_id")

		if subject:
			queryset = queryset.filter(subject__name__iexact=subject)
		if subject_id:
			queryset = queryset.filter(subject_id=subject_id)
		return queryset


class IndustryViewSet(viewsets.ModelViewSet):
	queryset = Industry.objects.select_related("branch__subject").all().order_by(
		"branch__subject__order", "branch__order", "order"
	)
	serializer_class = IndustrySerializer
	permission_classes = [IsAuthenticatedOrReadOnly]

	def get_queryset(self):
		queryset = super().get_queryset()
		subject = self.request.query_params.get("subject")
		branch = self.request.query_params.get("branch")
		branch_id = self.request.query_params.get("branch_id")

		if subject:
			queryset = queryset.filter(branch__subject__name__iexact=subject)
		if branch:
			queryset = queryset.filter(branch__name__iexact=branch)
		if branch_id:
			queryset = queryset.filter(branch_id=branch_id)
		return queryset


class SubIndustryViewSet(viewsets.ModelViewSet):
	queryset = SubIndustry.objects.select_related("industry__branch__subject").all().order_by(
		"industry__branch__subject__order", "industry__branch__order", "industry__order", "order"
	)
	serializer_class = SubIndustrySerializer
	permission_classes = [IsAuthenticatedOrReadOnly]

	def get_queryset(self):
		queryset = super().get_queryset()
		subject = self.request.query_params.get("subject")
		branch = self.request.query_params.get("branch")
		industry = self.request.query_params.get("industry")
		industry_id = self.request.query_params.get("industry_id")

		if subject:
			queryset = queryset.filter(industry__branch__subject__name__iexact=subject)
		if branch:
			queryset = queryset.filter(industry__branch__name__iexact=branch)
		if industry:
			queryset = queryset.filter(industry__name__iexact=industry)
		if industry_id:
			queryset = queryset.filter(industry_id=industry_id)
		return queryset


class TemporalSlotViewSet(viewsets.ModelViewSet):
	queryset = TemporalSlot.objects.all().order_by("position")
	serializer_class = TemporalSlotSerializer
	permission_classes = [IsAuthenticatedOrReadOnly]

	def get_queryset(self):
		queryset = super().get_queryset()
		tense = self.request.query_params.get("tense")
		phase = self.request.query_params.get("phase")

		if tense:
			queryset = queryset.filter(tense=tense)
		if phase:
			queryset = queryset.filter(default_phase=phase)
		return queryset


def _apply_lattice_filters(nodes, query_params):
	filtered = nodes
	subject = query_params.get("subject")
	branch = query_params.get("branch")
	industry = query_params.get("industry")
	tense = query_params.get("tense")
	phase = query_params.get("phase")
	position = query_params.get("position")

	if subject:
		filtered = [n for n in filtered if n["subject"].lower() == subject.lower()]
	if branch:
		filtered = [n for n in filtered if n["branch"].lower() == branch.lower()]
	if industry:
		filtered = [n for n in filtered if n["industry"].lower() == industry.lower()]
	if tense:
		filtered = [n for n in filtered if n["tense"] == tense]
	if phase:
		filtered = [n for n in filtered if n["phase"] == phase]
	if position:
		try:
			position_int = int(position)
			filtered = [n for n in filtered if n["position"] == position_int]
		except ValueError:
			pass
	return filtered


class LatticeMapView(APIView):
	def get(self, request):
		nodes = _apply_lattice_filters(build_lattice_nodes(), request.query_params)
		return Response({"count": len(nodes), "results": nodes})


class LatticeMapExportView(APIView):
	def get(self, request):
		nodes = _apply_lattice_filters(build_lattice_nodes(), request.query_params)
		export_format = request.query_params.get("export", "json").lower()

		if export_format == "csv":
			response = HttpResponse(content_type="text/csv")
			response["Content-Disposition"] = 'attachment; filename="btif_lattice_export.csv"'
			writer = csv.DictWriter(
				response,
				fieldnames=[
					"subject",
					"branch",
					"industry",
					"sub_industry",
					"sub_industry_order",
					"position",
					"tense",
					"color",
					"phase",
				],
			)
			writer.writeheader()
			writer.writerows(nodes)
			return response

		return Response({"count": len(nodes), "results": nodes})


class LinearHierarchyGenerateView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		subjects = request.data.get("subjects")
		reset = bool(request.data.get("reset", False))

		if not isinstance(subjects, list):
			return Response(
				{"detail": "subjects must be a list of exactly 4 ordered names."},
				status=400,
			)

		try:
			result = generate_linear_hierarchy(subjects, reset=reset)
		except ValueError as exc:
			return Response({"detail": str(exc)}, status=400)

		return Response({"detail": "Hierarchy generated.", **result}, status=201)
