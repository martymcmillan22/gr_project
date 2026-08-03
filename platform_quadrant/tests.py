from django.test import TestCase

from platform_quadrant.models import GICSReference
from platform_quadrant.models import NAICSReference
from platform_quadrant.models import SemanticBundle
from platform_quadrant.models import SemanticBundleRevision
from platform_quadrant.models import SemanticPreset
from platform_quadrant.models import Slide


class PlatformQuadrantActivationTests(TestCase):
	def _seed_minimum_semantic_assets(self):
		preset = SemanticPreset.objects.create(
			name="create.blue.quadrant",
			phase="create",
			color_primary="blue",
			metaphor="immune_system",
			dewey_code=120,
			ui_category="operations",
		)
		Slide.objects.create(
			title="Quadrant Activation Slide",
			phase="create",
			color_primary="blue",
			metaphor="immune_system",
			dewey_code=120,
			ui_category="operations",
			phase_resolved="create",
			ui_category_resolved="operations",
			layout_archetype="matrix",
			component_pack="pack_q",
			nav_group="group_q",
			page_signature="sig_q",
			applied_preset=preset,
		)
		bundle = SemanticBundle.objects.create(
			name="bundle.quadrant.activation",
			label="Quadrant Activation",
			family="foundation",
			sequence=[preset.name],
		)
		SemanticBundleRevision.objects.create(
			bundle=bundle,
			revision_number=1,
			label="Quadrant Activation v1",
			family="foundation",
			sequence=[preset.name],
		)

	def _seed_minimum_reference_truth(self):
		GICSReference.objects.create(
			code="15101010",
			name="Internet Services and Infrastructure",
			level=GICSReference.LEVEL_SUB_INDUSTRY,
			source_version="GICS-LICENSED-2026",
		)
		NAICSReference.objects.create(
			code="518210",
			title="Data Processing, Hosting, and Related Services",
			sector_code="51",
			source_version="NAICS-2022",
		)

	def test_health_endpoint_returns_active_boundary(self):
		response = self.client.get("/platform/quadrant/health/")
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["app"], "platform_quadrant")
		self.assertEqual(payload["status"], "active")

	def test_activation_endpoint_reports_expected_keys(self):
		response = self.client.get("/platform/quadrant/activation/")
		self.assertEqual(response.status_code, 200)
		payload = response.json()

		self.assertIn("resolver_clock", payload)
		self.assertIn("resolver_catalog", payload)
		self.assertIn("reference_truth", payload)
		self.assertIn("semantic_truth", payload)
		self.assertIn("classification_truth", payload)
		self.assertIn("capability_flags", payload)
		self.assertIn("deterministic_ready", payload)

	def test_activation_endpoint_can_become_deterministic_ready(self):
		self._seed_minimum_semantic_assets()
		self._seed_minimum_reference_truth()

		response = self.client.get("/platform/quadrant/activation/")
		self.assertEqual(response.status_code, 200)
		payload = response.json()

		self.assertTrue(payload["capability_flags"]["industry_hierarchy"])
		self.assertTrue(payload["capability_flags"]["temporal_slots"])
		self.assertTrue(payload["capability_flags"]["semantic_bundle_routing"])
		self.assertTrue(payload["capability_flags"]["reference_truth_binding"])
		self.assertTrue(payload["capability_flags"]["deterministic_quadrant_routing"])
		self.assertTrue(payload["deterministic_ready"])
