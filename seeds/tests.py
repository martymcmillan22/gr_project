from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from peringram.models import Industry, IndustryGroup, LatticeCompartment
from users.models import User

from .models import Business, CrossReference, Idea, Seed
from .services import validate_idea_submission


class IdeaLifecycleTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="seed-user", password="testpass123")
		self.group = IndustryGroup.objects.create(code=1, sector=IndustryGroup.SECTOR_PRIMARY, name="Math")
		self.industry = Industry.objects.create(group=self.group, code=1, name="Food Tech")

	def test_raw_to_seed_transition_creates_seed_with_json_metadata(self):
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
