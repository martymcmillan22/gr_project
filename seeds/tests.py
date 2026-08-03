from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from peringram.models import ConvectionCompartment, Industry, IndustryGroup, LatticeCompartment
from peringram.models import Recycle3Profile
from peringram.views import seed_peringram_structure
from users.models import User

from .models import Business, CrossReference, Idea, Seed
from .services import validate_idea_submission

# Phase 4 (PIP): RAW->SEED is now temporally gated (see seeds/signals.py),
# based on timezone.localtime() -> Convection-Cycle time_frame. Tests that
# transition an Idea to SEED must freeze the clock to a deterministic,
# allowed slot (hour 10 -> Convection compartment 11 -> lattice index 11 ->
# time_frame="present_future", which is in IDEA_TO_SEED_ALLOWED_TIME_FRAMES),
# so they don't flake depending on real-world wall-clock time.
FROZEN_ALLOWED_SLOT = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.get_current_timezone())


class IdeaLifecycleTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="seed-user", password="testpass123")
		self.group = IndustryGroup.objects.create(code=1, sector=IndustryGroup.SECTOR_PRIMARY, name="Math")
		self.industry = Industry.objects.create(group=self.group, code=1, name="Food Tech")
		# Phase 4: seed only the specific ConvectionCompartment/LatticeCompartment
		# rows the frozen-clock test needs (not the full seed_peringram_structure(),
		# which would rename this test's custom "Food Tech" industry back to the
		# default "Math - Foundation" via its own IndustryGroup/Industry seeding).
		ConvectionCompartment.objects.get_or_create(
			compartment_index=11,
			defaults={"world_clock_hour": 10, "label": "Compartment 11", "lattice_coordinate": "R11"},
		)
		LatticeCompartment.objects.get_or_create(
			index=11,
			defaults={
				"color": "Amber",
				"time_frame": LatticeCompartment.TIME_PRESENT_FUTURE,
				"capacity": 4 ** 11,
				"category": "Architecture",
			},
		)

	@patch("django.utils.timezone.localtime", return_value=FROZEN_ALLOWED_SLOT)
	def test_raw_to_seed_transition_creates_seed_with_json_metadata(self, mock_localtime):
		idea = Idea.objects.create(
			user=self.user,
			industry=self.industry,
			raw_content="Portable kitchen fermentation platform",
			status=Idea.STATUS_RAW,
		)

		idea.status = Idea.STATUS_SEED
		idea.save()

		seed = Seed.objects.get(idea=idea)
		self.assertEqual(seed.polish_notes["industry"]["name"], "Food Tech")
		self.assertIn("recipe", seed.polish_notes["requirements"])

	def test_seed_status_requires_content(self):
		idea = Idea(
			user=self.user,
			industry=self.industry,
			raw_content="   ",
			status=Idea.STATUS_SEED,
		)

		with self.assertRaises(ValidationError):
			idea.save()

	def test_industry_is_dynamic_fk_not_hard_coded(self):
		dynamic_industry = Industry.objects.create(group=self.group, code=2, name="Fintech")
		idea = Idea.objects.create(
			user=self.user,
			industry=dynamic_industry,
			raw_content="Embedded credit scoring layer",
			status=Idea.STATUS_RAW,
		)

		dynamic_industry.name = "Digital Finance"
		dynamic_industry.save(update_fields=["name"])
		idea.refresh_from_db()

		self.assertEqual(idea.industry.name, "Digital Finance")


class CrossReferenceModelTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="graph-user", password="testpass123")
		self.group = IndustryGroup.objects.create(code=1, sector=IndustryGroup.SECTOR_PRIMARY, name="Math")
		self.industry = Industry.objects.create(group=self.group, code=1, name="Food Tech")

		idea_a = Idea.objects.create(
			user=self.user,
			industry=self.industry,
			raw_content="Idea A",
			status=Idea.STATUS_RAW,
		)
		idea_b = Idea.objects.create(
			user=self.user,
			industry=self.industry,
			raw_content="Idea B",
			status=Idea.STATUS_RAW,
		)

		seed_a = Seed.objects.create(idea=idea_a)
		seed_b = Seed.objects.create(idea=idea_b)

		self.business_a = Business.objects.create(seed=seed_a, brand_name="A", market_status="ready")
		self.business_b = Business.objects.create(seed=seed_b, brand_name="B", market_status="ready")

	def test_unique_edge_per_relationship_type(self):
		CrossReference.objects.create(
			source_business=self.business_a,
			target_business=self.business_b,
			relationship_type=CrossReference.RELATION_SIMILAR,
			score=0.91,
		)

		with self.assertRaises(IntegrityError):
			CrossReference.objects.create(
				source_business=self.business_a,
				target_business=self.business_b,
				relationship_type=CrossReference.RELATION_SIMILAR,
				score=0.88,
			)

	def test_source_lookup_returns_best_scores_first(self):
		CrossReference.objects.create(
			source_business=self.business_a,
			target_business=self.business_b,
			relationship_type=CrossReference.RELATION_DEPENDS_ON,
			score=0.65,
		)
		CrossReference.objects.create(
			source_business=self.business_b,
			target_business=self.business_a,
			relationship_type=CrossReference.RELATION_DEPENDS_ON,
			score=0.95,
		)
		CrossReference.objects.create(
			source_business=self.business_a,
			target_business=self.business_b,
			relationship_type=CrossReference.RELATION_SUPPLIES,
			score=0.92,
		)

		edges = list(
			CrossReference.objects.filter(source_business=self.business_a)
			.values_list("relationship_type", "score")
		)

		self.assertEqual(edges[0][0], CrossReference.RELATION_SUPPLIES)
		self.assertEqual(float(edges[0][1]), 0.92)


class LatticeValidationTests(TestCase):
	def setUp(self):
		LatticeCompartment.objects.update_or_create(
			index=1,
			defaults={
				"color": "Red",
				"time_frame": LatticeCompartment.TIME_PAST,
				"capacity": 4,
				"category": "Math",
			},
		)
		LatticeCompartment.objects.update_or_create(
			index=8,
			defaults={
				"color": "Lime",
				"time_frame": LatticeCompartment.TIME_FUTURE,
				"capacity": 65536,
				"category": "Technology",
			},
		)

	def test_rejects_when_compartment_is_unknown(self):
		with self.assertRaises(ValidationError):
			validate_idea_submission(99, "abc", metadata={"tags": ["historical"]})

	def test_rejects_when_capacity_is_exceeded(self):
		result = validate_idea_submission(1, "abcdef", metadata={"tags": ["historical"]})
		self.assertEqual(result["status"], "rejected")
		self.assertEqual(result["reason"], "Content exceeds compartment capacity.")

	def test_rejects_when_future_tag_is_missing(self):
		result = validate_idea_submission(8, "launch AI assistant", metadata={"tags": ["planning"]})
		self.assertEqual(result["status"], "rejected")
		self.assertIn("forecast", result["reason"])

	def test_approves_when_constraints_are_met(self):
		result = validate_idea_submission(8, "launch AI assistant", metadata={"tags": ["forecast"]})
		self.assertEqual(result["status"], "approved")
		self.assertEqual(result["category"], "Technology")


class SeedsApiTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="api-user", password="testpass123")
		self.group = IndustryGroup.objects.create(code=1, sector=IndustryGroup.SECTOR_PRIMARY, name="Math")
		self.industry = Industry.objects.create(group=self.group, code=1, name="Technology")
		self.recycle3 = Recycle3Profile.objects.create(
			user=self.user,
			corporation_rnd_pct=Decimal("40.00"),
			people_qcqa_pct=Decimal("40.00"),
			government_infra_pct=Decimal("40.00"),
			isea_pct=Decimal("0.01"),
		)
		self.client.force_authenticate(user=self.user)

		idea_a = Idea.objects.create(
			user=self.user,
			industry=self.industry,
			raw_content="AI supply chain planner",
			status=Idea.STATUS_RAW,
		)
		idea_b = Idea.objects.create(
			user=self.user,
			industry=self.industry,
			raw_content="AI logistics forecast platform",
			status=Idea.STATUS_RAW,
		)
		seed_a = Seed.objects.create(idea=idea_a)
		seed_b = Seed.objects.create(idea=idea_b)
		self.business_a = Business.objects.create(seed=seed_a, brand_name="A", market_status="ready")
		self.business_b = Business.objects.create(seed=seed_b, brand_name="B", market_status="ready")
		CrossReference.objects.create(
			source_business=self.business_a,
			target_business=self.business_b,
			relationship_type=CrossReference.RELATION_SIMILAR,
			score=0.91,
		)
		seed_peringram_structure()

	def test_capture_endpoint_creates_raw_idea_and_returns_candidates(self):
		url = reverse("idea-capture")
		response = self.client.post(
			url,
			{
				"industry_id": self.industry.id,
				"raw_content": "AI logistics forecast for warehouses",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data["idea"]["status"], Idea.STATUS_RAW)
		self.assertGreaterEqual(len(response.data["cross_reference_candidate_ids"]), 1)

	def test_capture_endpoint_fails_on_lattice_validation(self):
		url = reverse("idea-capture")
		response = self.client.post(
			url,
			{
				"industry_id": self.industry.id,
				"raw_content": "future world model",
				"compartment_id": 8,
				"metadata": {"tags": ["planning"]},
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("lattice_validation", response.data)

	def test_cross_reference_endpoint_supports_filters(self):
		url = reverse("cross-reference-list")
		response = self.client.get(url, {"relationship_type": CrossReference.RELATION_SIMILAR})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data["results"]), 1)
		self.assertEqual(response.data["results"][0]["relationship_type"], CrossReference.RELATION_SIMILAR)

	@patch("django.utils.timezone.localtime", return_value=FROZEN_ALLOWED_SLOT)
	def test_seed_promotion_endpoint_creates_seed_and_returns_project_ready_payload(self, mock_localtime):
		url = reverse("seed-promote")
		response = self.client.post(
			url,
			{
				"purpose": "Basetrue Newsletter",
				"industry": "Media / Publishing",
				"audience": "Readers and contributors",
				"narrative": "A deterministic editorial project.",
				"notes": "Annual plan demo flow for ISPE.",
				"identity_name": "Basetrue Newsletter",
				"identity_type": "Editorial Identity",
				"identity_purpose": "Create a guided editorial identity.",
				"identity_structure": "Sections, themes, recurring elements.",
				"deliverables": "Monthly newsletter issues, annual summary",
				"deliverable_structure": "Lead story, recurring sections, checkpoints",
				"deliverable_cadence": "Monthly",
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(response.data["project_ready"])
		self.assertEqual(response.data["next_phase"], "project")
		self.assertEqual(response.data["idea"]["status"], Idea.STATUS_SEED)
		self.assertIn("promotion_context", response.data["seed"]["polish_notes"])
		self.assertEqual(
			response.data["seed"]["polish_notes"]["promotion_context"]["identity"]["name"],
			"Basetrue Newsletter",
		)

	@patch("django.utils.timezone.localtime", return_value=FROZEN_ALLOWED_SLOT)
	@patch("seeds.views.SRLService.assign_compartment")
	def test_project_activation_endpoint_creates_business_and_updates_seed_status(self, mock_assign_compartment, mock_localtime):
		mock_assign_compartment.return_value = LatticeCompartment.objects.get(index=3)
		seed_response = self.client.post(
			reverse("seed-promote"),
			{
				"purpose": "A",
				"industry": "Media / Publishing",
				"audience": "B",
				"narrative": "C",
				"notes": "D",
				"identity_name": "Basetrue Newsletter",
				"identity_type": "Editorial Identity",
				"identity_purpose": "Editorial identity",
				"identity_structure": "Sections",
				"deliverables": "Newsletter",
				"deliverable_structure": "Lead story",
				"deliverable_cadence": "Monthly",
			},
			format="json",
		)

		seed_id = seed_response.data["seed"]["id"]
		project_response = self.client.post(
			reverse("project-activate"),
			{
				"seed_id": seed_id,
				"project_name": "Basetrue Newsletter",
				"market_status": "live",
				"project_notes": {
					"annual_plan": "Editorial calendar, theme tracking, issue rhythm",
					"quarterly_objectives": "Q1 launch, Q2 consistency, Q3 refinement, Q4 recap",
					"monthly_deliverables": "Monthly newsletter issues, annual summary",
					"task_archetypes": ["Linear", "Perpetual"],
					"governance_tiers": ["PIP", "Polish", "Task Manager"],
				},
			},
			format="json",
		)

		self.assertEqual(project_response.status_code, status.HTTP_201_CREATED, project_response.data)
		self.assertTrue(project_response.data["project_ready"])
		self.assertEqual(project_response.data["business"]["brand_name"], "Basetrue Newsletter")
		self.assertEqual(project_response.data["business"]["market_status"], "live")
		self.assertEqual(project_response.data["business"]["project_notes"]["phase"], "project")
		self.assertEqual(Seed.objects.get(pk=seed_id).idea.status, Idea.STATUS_PROJECT)
