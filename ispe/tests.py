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
from platform_reference.models import PlatformReferenceGICSReferenceSchema, PlatformReferenceNAICSReferenceSchema
from project_middle_layer.models import ProjectEvolutionSnapshot, ProjectNode, SemanticAlert, SemanticLineageRecord


class ISPEActivationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.staff_user = user_model.objects.create_superuser(
            username="ispe_admin",
            email="ispe_admin@example.com",
            password="password12345",
        )

    def _seed_platform_ready_state(self):
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

        preset = SemanticPreset.objects.create(
            name="create.green.ispe",
            phase="create",
            color_primary="green",
            metaphor="immune_system",
            dewey_code=100,
            ui_category="operations",
        )
        Slide.objects.create(
            title="ISPE Activation Slide",
            phase="create",
            color_primary="green",
            metaphor="immune_system",
            dewey_code=100,
            ui_category="operations",
            phase_resolved="create",
            ui_category_resolved="operations",
            layout_archetype="matrix",
            component_pack="pack_ispe",
            nav_group="group_ispe",
            page_signature="sig_ispe",
            applied_preset=preset,
        )
        bundle = SemanticBundle.objects.create(
            name="bundle.ispe.activation",
            label="ISPE Activation",
            family="foundation",
            sequence=[preset.name],
            created_by=self.staff_user,
        )
        revision = SemanticBundleRevision.objects.create(
            bundle=bundle,
            revision_number=1,
            label="ISPE Activation v1",
            family="foundation",
            sequence=[preset.name],
            created_by=self.staff_user,
        )
        SemanticBundleRevisionTag.objects.create(
            bundle=bundle,
            revision=revision,
            name="stable",
            note="ISPE baseline",
            created_by=self.staff_user,
        )

        MLASClassificationRecord.objects.create(
            record_id="ISPE-001",
            source_name_raw="ISPE seed",
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

        node = ProjectNode.objects.create(
            slug="ispe-node",
            name="ISPE Node",
            semantic_intent="ExpandAndIntegrate",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
        )
        snapshot = ProjectEvolutionSnapshot.objects.create(
            project=node,
            identity_payload={"identity": {"identity_uri": "cpndc://ispe-node/ispe-node"}},
            drift_forecast={"risk": {"blended_semantic_drift_risk": 0.2}},
            branch_resolution={"selected_branch": "stabilization_branch"},
            specialized_path={"compile_status": "ready"},
            semantic_tags=["project", "semantic"],
            identity_uri="cpndc://ispe-node/ispe-node",
            branch_name="stabilization_branch",
            drift_risk=0.2,
            confidence_score=88,
            confidence_label="Stable",
            schema_issue_count=0,
            recommendations=["Keep cadence stable"],
        )
        SemanticLineageRecord.objects.create(
            project=node,
            lineage_tree={"node": "ispe-node"},
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

    def test_ispe_activation_endpoint_reports_heartbeat_state(self):
        response = self.client.get("/ispe/activation/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["app"], "ispe")
        self.assertEqual(payload["contract"], "ispe-orchestration-heartbeat")
        self.assertIn("activation_contract", payload)
        self.assertIn("orchestration_contract", payload)
        self.assertIn("phase_guidance", payload)
        self.assertIn("phase_policy", payload)
        self.assertIn("va_compartment_narration", payload)
        self.assertIn("polish_compartment_refinement", payload)
        self.assertIn("middle_layer_compartment_drift", payload)
        self.assertIn("ispe_ready", payload)
        self.assertIn("semantic_ready", payload)
        self.assertIn("quadrant_ready", payload)
        self.assertIn("middle_layer_ready", payload)
        self.assertFalse(payload["ispe_ready"])

    def test_ispe_activation_endpoint_can_become_ready(self):
        self._seed_platform_ready_state()

        response = self.client.get("/ispe/activation/?mode=assistive&phase=idea&include_va=1")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertTrue(payload["semantic_ready"])
        self.assertTrue(payload["quadrant_ready"])
        self.assertTrue(payload["middle_layer_ready"])
        self.assertTrue(payload["ispe_config_ready"])
        self.assertTrue(payload["ispe_ready"])
        self.assertEqual(payload["mode"], "assistive")
        self.assertEqual(payload["phase"], "idea")
        self.assertIn("next_suggested_fields", payload["phase_guidance"])
        self.assertIn("idea_title", payload["phase_guidance"]["next_suggested_fields"])
        self.assertIn("orchestration_contract", payload)

    def test_ispe_activation_seed_and_project_guidance_resolve(self):
        self._seed_platform_ready_state()

        seed_response = self.client.get("/ispe/activation/?phase=seed")
        project_response = self.client.get("/ispe/activation/?phase=project")

        self.assertEqual(seed_response.status_code, 200)
        self.assertEqual(project_response.status_code, 200)
        seed_payload = seed_response.json()
        project_payload = project_response.json()

        self.assertEqual(seed_payload["phase"], "seed")
        self.assertEqual(project_payload["phase"], "project")
        self.assertIn("btif_identity", seed_payload["phase_guidance"]["next_suggested_fields"])
        self.assertIn("task_manager", project_payload["phase_guidance"]["primary_unlocks"])
        self.assertEqual(seed_payload["phase_policy"]["task_manager"]["enabled"], False)
        self.assertEqual(project_payload["phase_policy"]["task_manager"]["enabled"], True)
        self.assertTrue(len(project_payload["va_compartment_narration"]["compartments"]) > 0)
        self.assertTrue(len(project_payload["polish_compartment_refinement"]["compartments"]) > 0)
        self.assertTrue(len(project_payload["middle_layer_compartment_drift"]["compartments"]) > 0)
