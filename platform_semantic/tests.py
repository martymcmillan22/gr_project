from django.contrib.auth import get_user_model
from django.test import TestCase

from platform_semantic.models import GICSReference
from platform_semantic.models import MLASClassificationRecord
from platform_semantic.models import NAICSReference
from platform_semantic.models import SemanticBundle
from platform_semantic.models import SemanticBundleRevision
from platform_semantic.models import SemanticBundleRevisionTag
from platform_semantic.models import SemanticPreset
from platform_semantic.models import Slide


class PlatformSemanticActivationTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		user_model = get_user_model()
		cls.staff_user = user_model.objects.create_superuser(
			username="platform_semantic_admin",
			email="platform_semantic_admin@example.com",
			password="password12345",
		)

	def _seed_minimum_semantic_assets(self):
		preset = SemanticPreset.objects.create(
			name="create.red.test",
			phase="create",
			color_primary="red",
			metaphor="immune_system",
			dewey_code=100,
			ui_category="operations",
		)
		Slide.objects.create(
			title="Activation Slide",
			phase="create",
			color_primary="red",
			metaphor="immune_system",
			dewey_code=100,
			ui_category="operations",
			phase_resolved="create",
			ui_category_resolved="operations",
			layout_archetype="matrix",
			component_pack="pack_a",
			nav_group="group_a",
			page_signature="sig_a",
			applied_preset=preset,
		)
		bundle = SemanticBundle.objects.create(
			name="bundle.activation",
			label="Activation",
			family="foundation",
			sequence=[preset.name],
			created_by=self.staff_user,
		)
		revision = SemanticBundleRevision.objects.create(
			bundle=bundle,
			revision_number=1,
			label="Activation v1",
			family="foundation",
			sequence=[preset.name],
			created_by=self.staff_user,
		)
		SemanticBundleRevisionTag.objects.create(
			bundle=bundle,
			revision=revision,
			name="stable",
			note="Activation baseline",
			created_by=self.staff_user,
		)

	def _seed_minimum_reference_truth(self):
		GICSReference.objects.create(
			code="10101010",
			name="Energy Equipment and Services",
			level=GICSReference.LEVEL_SUB_INDUSTRY,
			source_version="GICS-LICENSED-2026",
		)
		NAICSReference.objects.create(
			code="111110",
			title="Soybean Farming",
			sector_code="11",
			source_version="NAICS-2022",
		)

	def _seed_minimum_classification_truth(self):
		MLASClassificationRecord.objects.create(
			record_id="SEMANTIC-001",
			source_name_raw="Seed record",
			target_layer=MLASClassificationRecord.TARGET_TERM,
			mlas_subject_code="MATH",
			mlas_branch_code="SACP",
			mlas_term_code="CNIC",
			dewey_code="630",
			gics_sub_industry_code="10101010",
			naics_code_6="111110",
			algorithm_1_score=0.95,
			algorithm_2_score=0.95,
			algorithm_3_score=0.95,
			algorithm_4_score=0.95,
			confidence_overall=0.95,
			review_status=MLASClassificationRecord.REVIEW_APPROVED,
			reviewer=self.staff_user,
			reviewed_at="2026-01-01T00:00:00Z",
		)

	def test_health_endpoint_returns_active_boundary(self):
		response = self.client.get("/platform/semantic/health/")
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["app"], "platform_semantic")
		self.assertEqual(payload["status"], "active")

	def test_activation_endpoint_reports_expected_keys(self):
		response = self.client.get("/platform/semantic/activation/")
		self.assertEqual(response.status_code, 200)
		payload = response.json()

		self.assertIn("semantic_assets", payload)
		self.assertIn("reference_truth", payload)
		self.assertIn("classification_truth", payload)
		self.assertIn("semantic_catalogs", payload)
		self.assertIn("capability_flags", payload)
		self.assertIn("deterministic_ready", payload)

	def test_activation_endpoint_can_become_deterministic_ready(self):
		self._seed_minimum_semantic_assets()
		self._seed_minimum_reference_truth()
		self._seed_minimum_classification_truth()

		response = self.client.get("/platform/semantic/activation/")
		self.assertEqual(response.status_code, 200)
		payload = response.json()

		self.assertTrue(payload["capability_flags"]["semantic_pipelines"])
		self.assertTrue(payload["capability_flags"]["semantic_schedules"])
		self.assertTrue(payload["capability_flags"]["semantic_analytics"])
		self.assertTrue(payload["capability_flags"]["semantic_merge"])
		self.assertTrue(payload["capability_flags"]["semantic_versioning"])
		self.assertTrue(payload["deterministic_ready"])


class PlatformSemanticColorPreviewTests(TestCase):
	def test_subject_grid_view_renders_catalog(self):
		response = self.client.get("/platform/semantic/subject-grid/")
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Semantic Subject Grid")
		self.assertContains(response, "Math")
		self.assertContains(response, "Systemics")

	def test_color_preview_catalog_mode(self):
		response = self.client.get("/platform/semantic/color-preview/", {"catalog": "1"})
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["mode"], "catalog")
		self.assertEqual(len(payload["compartments"]), 16)
		self.assertEqual(payload["compartments"][0]["subject"], "Math")
		self.assertEqual(payload["compartments"][15]["subject"], "Systemics")

	def test_color_preview_from_ontology_path(self):
		response = self.client.get(
			"/platform/semantic/color-preview/",
			{
				"sector": "Primary",
				"subject": "Math",
				"industry": "Capital Markets",
				"subindustry": "Algorithmic Trading Systems & Quantitative Analysis",
				"node_index": 0,
			},
		)
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["mode"], "ontology_path")
		self.assertEqual(payload["compartment_id"], 0)
		self.assertEqual(payload["identity_rgb"], [0, 0, 0])
		self.assertEqual(payload["display_rgb"], [192, 0, 0])

	def test_color_preview_from_color_code(self):
		response = self.client.get("/platform/semantic/color-preview/", {"color_code": 9})
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["mode"], "color_code")
		self.assertEqual(payload["compartment_id"], 0)
		self.assertEqual(payload["local_index_fields"]["node_index"], 9)
		self.assertEqual(payload["identity_rgb"], [0, 0, 9])

	def test_color_preview_from_phase4_ontology_path(self):
		response = self.client.get(
			"/platform/semantic/color-preview/",
			{
				"sector": "Quaternary",
				"subject": "Economics",
				"industry": "Banking",
				"subindustry": "Central Bank Reserve Interventions & Fractional Lending Math",
				"node_index": 5,
			},
		)
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["mode"], "ontology_path")
		self.assertEqual(payload["compartment_id"], 14)
		self.assertEqual(payload["identity_rgb"], [224, 0, 5])

	def test_color_preview_missing_inputs_returns_400(self):
		response = self.client.get("/platform/semantic/color-preview/")
		self.assertEqual(response.status_code, 400)
		payload = response.json()
		self.assertIn("detail", payload)
