from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from platform_core.models import (
    MLASClassificationRecord,
    SemanticBundle,
    SemanticBundleRevision,
    SemanticBundleRevisionTag,
    SemanticPreset,
    Slide,
)
from platform_reference.models import (
    PlatformReferenceGICSReferenceSchema,
    PlatformReferenceNAICSReferenceSchema,
)
from project_middle_layer.models import (
    ProjectEvolutionSnapshot,
    ProjectNode,
    SemanticAlert,
    SemanticLineageRecord,
)


class Phase4ActivationEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.staff_user = user_model.objects.create_superuser(
            username="phase4_activation_admin",
            email="phase4_activation_admin@example.com",
            password="password12345",
        )

    def _seed_reference_truth(self):
        PlatformReferenceGICSReferenceSchema.objects.create(
            code="15101010",
            name="Internet Services and Infrastructure",
            level=PlatformReferenceGICSReferenceSchema.LEVEL_SUB_INDUSTRY,
            source_version="GICS-LICENSED-2026",
        )
        PlatformReferenceNAICSReferenceSchema.objects.create(
            code="518210",
            title="Data Processing, Hosting, and Related Services",
            sector_code="51",
            source_version="NAICS-2022",
        )

    def _seed_semantic_truth(self):
        preset = SemanticPreset.objects.create(
            name="create.red.phase4",
            phase="create",
            color_primary="red",
            metaphor="immune_system",
            dewey_code=100,
            ui_category="operations",
        )
        Slide.objects.create(
            title="Phase-4 Activation Slide",
            phase="create",
            color_primary="red",
            metaphor="immune_system",
            dewey_code=100,
            ui_category="operations",
            phase_resolved="create",
            ui_category_resolved="operations",
            layout_archetype="matrix",
            component_pack="pack_phase4",
            nav_group="group_phase4",
            page_signature="sig_phase4",
            applied_preset=preset,
        )
        bundle = SemanticBundle.objects.create(
            name="bundle.phase4.activation",
            label="Phase-4 Activation",
            family="foundation",
            sequence=[preset.name],
            created_by=self.staff_user,
        )
        revision = SemanticBundleRevision.objects.create(
            bundle=bundle,
            revision_number=1,
            label="Phase-4 Activation v1",
            family="foundation",
            sequence=[preset.name],
            created_by=self.staff_user,
        )
        SemanticBundleRevisionTag.objects.create(
            bundle=bundle,
            revision=revision,
            name="stable",
            note="Phase-4 baseline",
            created_by=self.staff_user,
        )

    def _seed_classification_truth(self):
        MLASClassificationRecord.objects.create(
            record_id="PHASE4-001",
            source_name_raw="Phase-4 seed",
            target_layer=MLASClassificationRecord.TARGET_TERM,
            mlas_subject_code="MATH",
            mlas_branch_code="SACP",
            mlas_term_code="CNIC",
            dewey_code="630",
            gics_sub_industry_code="15101010",
            naics_code_6="518210",
            quadrant_slug="quadrant-alpha",
            algorithm_1_score=0.95,
            algorithm_2_score=0.95,
            algorithm_3_score=0.95,
            algorithm_4_score=0.95,
            confidence_overall=0.95,
            review_status=MLASClassificationRecord.REVIEW_APPROVED,
            reviewer=self.staff_user,
            reviewed_at=timezone.now(),
        )

    def _seed_project_middle_layer_state(self):
        node = ProjectNode.objects.create(
            slug="phase4-node",
            name="Phase-4 Node",
            semantic_intent="ExpandAndIntegrate",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
        )
        snapshot = ProjectEvolutionSnapshot.objects.create(
            project=node,
            identity_payload={"identity": {"identity_uri": "cpndc://phase4-node/phase4-node"}},
            drift_forecast={"risk": {"blended_semantic_drift_risk": 0.2}},
            branch_resolution={"selected_branch": "stabilization_branch"},
            specialized_path={"compile_status": "ready"},
            semantic_tags=["project", "semantic"],
            identity_uri="cpndc://phase4-node/phase4-node",
            branch_name="stabilization_branch",
            drift_risk=0.2,
            confidence_score=88,
            confidence_label="Stable",
            schema_issue_count=0,
            recommendations=["Maintain baseline cadence"],
        )
        SemanticLineageRecord.objects.create(
            project=node,
            lineage_tree={"node": "phase4-node"},
            semantic_clusters=["foundation"],
            recommendations=["Monitor drift monthly"],
        )
        SemanticAlert.objects.create(
            project=node,
            source_snapshot=snapshot,
            alert_type="low_confidence",
            severity="low",
            message="Confidence stable",
            metadata={"score": 88},
        )

    def test_phase4_activation_endpoint_returns_unified_contract(self):
        response = self.client.get("/platform/activation/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["app"], "platform_activation")
        self.assertEqual(payload["contract"], "semantic-spine-heartbeat")
        self.assertIn("semantic_readiness", payload)
        self.assertIn("quadrant_readiness", payload)
        self.assertIn("project_middle_layer_readiness", payload)
        self.assertIn("phase_flags", payload)
        self.assertIn("deterministic_ready", payload)
        self.assertNotIn("va_readiness", payload)
        self.assertIn("request_context", payload)
        self.assertEqual(payload["request_context"]["mode"], "default")
        self.assertFalse(payload["request_context"]["policy_applied"])

    def test_phase4_activation_endpoint_includes_va_readiness_when_requested(self):
        response = self.client.get("/platform/activation/?include_va=1")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn("va_readiness", payload)
        self.assertIn("personality_load_state", payload["va_readiness"])
        self.assertIn("orchestration_available", payload["va_readiness"])
        self.assertIn("semantic_bridge_ready", payload["va_readiness"])
        self.assertIn("narrative_engine_ready", payload["va_readiness"])
        self.assertIn("deterministic_ready", payload["va_readiness"])
        self.assertTrue(payload["request_context"]["include_va"])

    def test_phase4_activation_endpoint_echoes_mode_for_correlation_only(self):
        response = self.client.get("/platform/activation/?mode=strict")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["request_context"]["mode"], "strict")
        self.assertFalse(payload["request_context"]["policy_applied"])
        self.assertIn("descriptive", payload["request_context"]["policy_note"].lower())

    def test_phase4_activation_endpoint_normalizes_unknown_mode_to_default(self):
        response = self.client.get("/platform/activation/?mode=unexpected")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["request_context"]["mode"], "default")

    def test_phase4_activation_endpoint_can_become_deterministic_ready(self):
        self._seed_reference_truth()
        self._seed_semantic_truth()
        self._seed_classification_truth()
        self._seed_project_middle_layer_state()

        response = self.client.get("/platform/activation/?include_va=1")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertTrue(payload["semantic_readiness"]["deterministic_ready"])
        self.assertTrue(payload["quadrant_readiness"]["deterministic_ready"])
        self.assertTrue(payload["project_middle_layer_readiness"]["deterministic_ready"])
        self.assertTrue(payload["va_readiness"]["deterministic_ready"])
        self.assertTrue(payload["deterministic_ready"])

    def test_phase4_orchestration_endpoint_returns_decision_contract(self):
        response = self.client.get("/platform/orchestration/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["contract"], "semantic-spine-orchestration")
        self.assertEqual(payload["contract_version"], "1.0.0")
        self.assertEqual(payload["phase"], 4)
        self.assertTrue(payload["decision_surface"])
        self.assertIn("decision", payload)
        self.assertIn("blocking_capabilities", payload)
        self.assertIn("missing_dependencies", payload)
        self.assertIn("readiness_gates", payload)
        self.assertIn("activation_sequence", payload)
        self.assertIn("recommended_next_actions", payload)
        self.assertIn("orchestration_hints", payload)
        self.assertIn("semantic_spine_health_summary", payload)
        self.assertFalse(payload["decision"]["go"])
        self.assertEqual(payload["decision"]["state"], "no-go")

    def test_phase4_orchestration_endpoint_includes_va_when_requested(self):
        response = self.client.get("/platform/orchestration/?include_va=1")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn("va_readiness", payload)
        self.assertIn("orchestration_available", payload["va_readiness"])
        self.assertIn("mode", payload["orchestration_hints"]["va"])

    def test_phase4_orchestration_endpoint_can_return_go(self):
        self._seed_reference_truth()
        self._seed_semantic_truth()
        self._seed_classification_truth()
        self._seed_project_middle_layer_state()

        response = self.client.get("/platform/orchestration/?include_va=1")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertTrue(payload["decision"]["go"])
        self.assertEqual(payload["decision"]["state"], "go")
        self.assertEqual(payload["decision"]["platform_wide_activation_state"], "active")
        self.assertEqual(payload["blocking_capabilities"], [])
        self.assertTrue(payload["deterministic_ready"])

    def test_phase4_orchestration_strict_mode_is_unforgiving(self):
        response = self.client.get("/platform/orchestration/?mode=strict")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["policy"]["mode"], "strict")
        self.assertFalse(payload["decision"]["go"])
        self.assertEqual(payload["decision"]["state"], "no-go")
        self.assertGreater(len(payload["blocking_capabilities"]), 0)
        self.assertEqual(payload["recommended_next_actions"], [])

    def test_phase4_orchestration_assistive_mode_allows_soft_blockers(self):
        self._seed_reference_truth()
        self._seed_semantic_truth()
        self._seed_classification_truth()
        self._seed_project_middle_layer_state()

        response = self.client.get("/platform/orchestration/?mode=assistive")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["policy"]["mode"], "assistive")
        self.assertTrue(payload["decision"]["go"])
        self.assertEqual(payload["decision"]["platform_wide_activation_state"], "active_with_soft_blockers")
        self.assertEqual(payload["blocking_capabilities"], [])
        self.assertGreater(len(payload["soft_blocking_capabilities"]), 0)
        self.assertGreater(len(payload["recommended_next_actions"]), 0)
        self.assertEqual(payload["orchestration_hints"]["ui"]["mode"], "guided_activation")
