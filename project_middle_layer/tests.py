import json

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from unittest.mock import MagicMock, patch
from rest_framework import status
from rest_framework.test import APITestCase

from project_middle_layer.models import (
    DistributedAgentRun,
    ExternalAgent,
    FederationPeer,
    MarketplaceItem,
    MarketplaceVersion,
    ProjectEvolutionSnapshot,
    ProjectNode,
    ReplicationConfig,
    SemanticCrossSyncLog,
    SemanticExtension,
    SemanticAlert,
    SemanticAnalyticsSnapshot,
    SemanticAgentRun,
    SemanticAuditLog,
    SemanticChangeRequest,
    SemanticEditSession,
    SemanticLineageRecord,
    SemanticPermission,
    SemanticPipeline,
    SemanticPipelineRun,
    SemanticRole,
    SemanticSchedule,
    SemanticScheduleRun,
    SemanticShard,
    SemanticSyncLog,
    SemanticPlugin,
    SemanticUserProfile,
    SemanticVersion,
    SemanticWebhook,
    SemanticWebhookDelivery,
    SemanticIntegration,
)
from project_middle_layer.pipelines import build_project_creation_payload
from project_middle_layer.lfo_engine import (
    build_consumer_gui_science_surface,
    build_industry_lfo_templates,
    build_lfo_engine_envelope,
    build_micro_lfo_templates,
    build_sevm_group_templates,
    evaluate_feature_probability,
    load_macro_industry_groups,
)
from project_middle_layer.services import build_calculus_timeline_runtime_payload
from project_middle_layer.services import dispatch_calculus_timeline_runtime_events
from project_middle_layer.webhooks import dispatch_semantic_webhook_event
from project_middle_layer.webhooks import retry_webhook_delivery
from platform_reference.models import PlatformReferenceGICSReferenceSchema
from platform_reference.models import PlatformReferenceNAICSReferenceSchema
from users.models import User


class ProjectMiddleLayerPipelineTests(SimpleTestCase):
    def test_build_project_creation_payload_contains_required_sections(self):
        payload = build_project_creation_payload(
            slug="project-middle-layer",
            name="Project Middle Layer",
            semantic_intent="ExpandAndIntegrate",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            semantic_tags=["project", "semantic", "identity", "pipeline", "tier", "compiler"],
        )

        self.assertIn("projects_json_schema", payload)
        self.assertIn("schema", payload)
        self.assertIn("schema_validation_errors", payload)
        self.assertIn("tier_profile", payload)
        self.assertIn("identity_payload", payload)
        self.assertIn("specialized_path", payload)
        self.assertIn("semantic_tree", payload)
        self.assertIn("drift_forecast", payload)
        self.assertIn("confidence", payload)
        self.assertIn("lineage_explorer", payload)
        self.assertIn("drift_heatmap_data", payload)
        self.assertIn("stability_analysis", payload)
        self.assertIn("recommendations", payload)
        self.assertIn("semantic_alerts", payload)
        self.assertEqual(payload["schema_validation_errors"], [])
        self.assertIn("cpndc://project-middle-layer/project-middle-layer", payload["identity_payload"]["identity"]["identity_uri"])
        self.assertIn("identity_id", payload["identity_payload"]["identity"])
        self.assertIn("branch_resolution", payload["identity_payload"]["identity"])
        self.assertIn(
            payload["identity_payload"]["identity"]["branch_resolution"]["selected_branch"],
            ["stabilization_branch", "expansion_integration_branch"],
        )
        self.assertIn("IDEA", payload["tier_profile"]["lifecycle"])
        self.assertIn("SPECIALIZED_PATH", payload["tier_profile"]["lifecycle"])
        self.assertIn("Identity Branch", payload["semantic_tree"])
        self.assertIn("risk", payload["drift_forecast"])
        self.assertIn("blended_semantic_drift_risk", payload["drift_forecast"]["risk"])
        self.assertEqual(payload["specialized_path"]["compile_status"], "ready")
        self.assertIn("forms", payload["specialized_path"])
        self.assertIn("final_identity_uri", payload["specialized_path"]["forms"][0])


class ProjectMiddleLayerRouteTests(SimpleTestCase):
    def test_api_compile_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-compile"),
            "/project-middle-layer/api/compile/",
        )

    def test_api_wizard_routes_resolve(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-wizard-start"),
            "/project-middle-layer/api/wizard/start/",
        )

    def test_compile_page_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:compile"),
            "/project-middle-layer/compile/",
        )

    def test_activation_page_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:activation"),
            "/project-middle-layer/activation/",
        )

    def test_lineage_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:lineage"),
            "/project-middle-layer/lineage/",
        )

    def test_alerts_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:alerts"),
            "/project-middle-layer/alerts/",
        )

    def test_recommendations_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:recommendations"),
            "/project-middle-layer/recommendations/",
        )

    def test_batch_compile_page_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:batch-compile"),
            "/project-middle-layer/batch-compile/",
        )

    def test_diff_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:diff"),
            "/project-middle-layer/diff/",
        )

    def test_api_batch_compile_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-compile-batch"),
            "/project-middle-layer/api/compile/batch/",
        )

    def test_export_page_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:export"),
            "/project-middle-layer/export/",
        )

    def test_api_export_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-export"),
            "/project-middle-layer/api/export/",
        )

    def test_pipelines_page_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:pipelines"),
            "/project-middle-layer/pipelines/",
        )

    def test_api_pipeline_run_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-pipeline-run"),
            "/project-middle-layer/api/pipelines/run/",
        )

    def test_schedules_page_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:schedules"),
            "/project-middle-layer/schedules/",
        )

    def test_api_schedule_run_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-schedule-run"),
            "/project-middle-layer/api/schedules/run/",
        )

    def test_webhooks_page_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:webhooks"),
            "/project-middle-layer/webhooks/",
        )

    def test_webhook_retry_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:webhook-retry", kwargs={"delivery_id": 1}),
            "/project-middle-layer/webhooks/deliveries/1/retry/",
        )

    def test_integrations_page_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:integrations"),
            "/project-middle-layer/integrations/",
        )

    def test_analytics_page_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:analytics"),
            "/project-middle-layer/analytics/",
        )

    def test_dashboard_page_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:dashboard"),
            "/project-middle-layer/dashboard/",
        )

    def test_search_page_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:search"),
            "/project-middle-layer/search/",
        )

    def test_insights_page_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:insights"),
            "/project-middle-layer/insights/",
        )

    def test_agents_page_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:agents"),
            "/project-middle-layer/agents/",
        )

    def test_api_integration_inbound_sync_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-integration-inbound-sync"),
            "/project-middle-layer/api/integrations/inbound-sync/",
        )

    def test_api_integration_outbound_sync_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-integration-outbound-sync"),
            "/project-middle-layer/api/integrations/outbound-sync/",
        )

    def test_api_search_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-search"),
            "/project-middle-layer/api/search/",
        )

    def test_api_analytics_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-analytics"),
            "/project-middle-layer/api/analytics/",
        )

    def test_roles_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:roles"),
            "/project-middle-layer/roles/",
        )

    def test_collaboration_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:collaboration"),
            "/project-middle-layer/collaboration/",
        )

    def test_change_requests_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:change-requests"),
            "/project-middle-layer/change-requests/",
        )

    def test_audit_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:audit"),
            "/project-middle-layer/audit/",
        )

    def test_versions_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:versions"),
            "/project-middle-layer/versions/",
        )

    def test_merge_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:merge"),
            "/project-middle-layer/merge/",
        )

    def test_api_version_commit_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-version-commit"),
            "/project-middle-layer/api/versions/commit/",
        )

    def test_api_version_checkout_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-version-checkout"),
            "/project-middle-layer/api/versions/checkout/",
        )

    def test_api_merge_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-merge"),
            "/project-middle-layer/api/merge/",
        )

    def test_api_collaboration_acquire_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-collaboration-session-acquire"),
            "/project-middle-layer/api/collaboration/sessions/acquire/",
        )

    def test_api_collaboration_heartbeat_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-collaboration-session-heartbeat"),
            "/project-middle-layer/api/collaboration/sessions/heartbeat/",
        )

    def test_api_collaboration_release_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-collaboration-session-release"),
            "/project-middle-layer/api/collaboration/sessions/release/",
        )

    def test_replication_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:replication"),
            "/project-middle-layer/replication/",
        )

    def test_federation_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:federation"),
            "/project-middle-layer/federation/",
        )

    def test_shards_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:shards"),
            "/project-middle-layer/shards/",
        )

    def test_cache_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:cache"),
            "/project-middle-layer/cache/",
        )

    def test_sync_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:sync"),
            "/project-middle-layer/sync/",
        )

    def test_distributed_agents_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:distributed-agents"),
            "/project-middle-layer/distributed-agents/",
        )

    def test_marketplace_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:marketplace"),
            "/project-middle-layer/marketplace/",
        )

    def test_plugins_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:plugins"),
            "/project-middle-layer/plugins/",
        )

    def test_extensions_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:extensions"),
            "/project-middle-layer/extensions/",
        )

    def test_gateway_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:gateway"),
            "/project-middle-layer/gateway/",
        )

    def test_btif_plus_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:btif-plus"),
            "/project-middle-layer/btif-plus/",
        )

    def test_external_agents_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:external-agents"),
            "/project-middle-layer/external-agents/",
        )

    def test_cross_sync_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:cross-sync"),
            "/project-middle-layer/cross-sync/",
        )

    def test_seed_demo_data_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:seed-demo-data"),
            "/project-middle-layer/seed-demo-data/",
        )

    def test_api_marketplace_install_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-marketplace-install"),
            "/project-middle-layer/api/marketplace/install/",
        )

    def test_api_lfo_engine_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-lfo-engine"),
            "/project-middle-layer/api/lfo/engine/",
        )

    def test_api_gateway_dispatch_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-gateway-dispatch"),
            "/project-middle-layer/api/gateway/dispatch/",
        )

    def test_api_btif_export_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-btif-plus-export"),
            "/project-middle-layer/api/btif-plus/export/",
        )

    def test_api_external_agent_run_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-external-agent-run"),
            "/project-middle-layer/api/external-agents/run/",
        )

    def test_api_cross_sync_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-cross-sync-run"),
            "/project-middle-layer/api/cross-sync/run/",
        )

    def test_api_calculus_timeline_runtime_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-calculus-timeline-runtime"),
            "/project-middle-layer/api/timeline/calculus/",
        )


class ProjectMiddleLayerActivationTests(TestCase):
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

    def _seed_semantic_state(self):
        node = ProjectNode.objects.create(
            slug="activation-node",
            name="Activation Node",
            semantic_intent="ExpandAndIntegrate",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
        )
        snapshot = ProjectEvolutionSnapshot.objects.create(
            project=node,
            identity_payload={"identity": {"identity_uri": "cpndc://activation-node/activation-node"}},
            drift_forecast={"risk": {"blended_semantic_drift_risk": 0.21}},
            branch_resolution={"selected_branch": "stabilization_branch"},
            specialized_path={"compile_status": "ready"},
            semantic_tags=["project", "semantic"],
            identity_uri="cpndc://activation-node/activation-node",
            branch_name="stabilization_branch",
            drift_risk=0.21,
            confidence_score=90,
            confidence_label="Stable",
            schema_issue_count=0,
            recommendations=["Keep cadence stable"],
        )
        SemanticLineageRecord.objects.create(
            project=node,
            lineage_tree={"node": "activation-node"},
            semantic_clusters=["foundation"],
            recommendations=["Monitor drift monthly"],
        )
        SemanticAlert.objects.create(
            project=node,
            source_snapshot=snapshot,
            alert_type="low_confidence",
            severity="low",
            message="Confidence stable",
            metadata={"score": 90},
        )

    def test_activation_endpoint_reports_expected_keys(self):
        response = self.client.get("/project-middle-layer/activation/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn("reference_truth", payload)
        self.assertIn("classification_truth", payload)
        self.assertIn("semantic_state", payload)
        self.assertIn("rr_color_context", payload)
        self.assertIn("capability_flags", payload)
        self.assertIn("compartment_drift_detection", payload)
        self.assertIn("deterministic_ready", payload)

    def test_activation_endpoint_can_become_deterministic_ready(self):
        self._seed_reference_truth()
        self._seed_semantic_state()

        response = self.client.get("/project-middle-layer/activation/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["reference_truth"]["gics_source_status"], "licensed")
        self.assertTrue(payload["capability_flags"]["canonical_reference_truth"])
        self.assertTrue(payload["capability_flags"]["classification_truth_binding"])
        self.assertTrue(payload["capability_flags"]["drift_signal_readiness"])
        self.assertTrue(payload["capability_flags"]["compile_export_chain"])
        self.assertTrue(payload["capability_flags"]["analytics_alert_surface"])
        self.assertTrue(payload["capability_flags"]["compartment_drift_governance"])
        self.assertIn("drift_baseline", payload["semantic_state"])
        self.assertTrue(len(payload["compartment_drift_detection"]["compartments"]) > 0)
        self.assertEqual(payload["rr_color_context"]["lane_count"], 16)
        self.assertIn("integrity_strip", payload["rr_color_context"])
        self.assertTrue(payload["deterministic_ready"])


class ProjectMiddleLayerCalculusTimelineAPITests(APITestCase):
    def test_calculus_timeline_runtime_returns_16_slots(self):
        url = reverse("project_middle_layer:project-middle-layer-calculus-timeline-runtime")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payload = response.data
        self.assertEqual(payload["mode"], "calculus_temporal_timeline_runtime")
        self.assertEqual(payload["timeline"]["slot_count"], 16)
        self.assertEqual(len(payload["slots"]), 16)
        self.assertIn("selected_slot_state", payload)
        self.assertIn("deterministic_progression", payload)

    def test_calculus_timeline_runtime_enforces_phase_gating(self):
        url = reverse("project_middle_layer:project-middle-layer-calculus-timeline-runtime")
        response = self.client.post(
            url,
            {
                "selected_slot": 6,
                "completed_slots": [1, 2, 3],
                "slot_content": {
                    "6": "continuity bridge transition sequence with publishing readiness",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payload = response.data
        seeds_gate = next(item for item in payload["deterministic_progression"]["phase_gates"] if item["phase"] == "Seeds")
        self.assertTrue(seeds_gate["locked"])

        selected = payload["selected_slot_state"]
        self.assertEqual(selected["slot_index"], 6)
        self.assertTrue(selected["gate"]["locked"])
        self.assertIn("state", selected)
        self.assertIn("drift_score", selected["state"])
        self.assertIn("industry_metadata", selected)

    def test_calculus_timeline_runtime_unlocks_seed_after_ideas_complete(self):
        url = reverse("project_middle_layer:project-middle-layer-calculus-timeline-runtime")
        response = self.client.post(
            url,
            {
                "selected_slot": 6,
                "completed_slots": [1, 2, 3, 4],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payload = response.data
        seeds_gate = next(item for item in payload["deterministic_progression"]["phase_gates"] if item["phase"] == "Seeds")
        self.assertFalse(seeds_gate["locked"])

        selected = payload["selected_slot_state"]
        self.assertFalse(selected["gate"]["locked"])

    def test_calculus_timeline_runtime_rejects_malformed_payload_shape(self):
        url = reverse("project_middle_layer:project-middle-layer-calculus-timeline-runtime")
        response = self.client.post(
            url,
            {
                "slot_content": ["invalid", "list"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_calculus_timeline_runtime_normalizes_partial_payloads(self):
        url = reverse("project_middle_layer:project-middle-layer-calculus-timeline-runtime")
        response = self.client.post(
            url,
            {
                "completed_slots": [1, 1, 2, 2, 3],
                "slot_content": {
                    "2": " continuity bridge ",
                    "not-a-slot": "ignored",
                },
                "prior_slot_states": {
                    "2": {"drift_score": 0.4, "alignment_score": 0.6, "gate_locked": False, "completed": False},
                    "bad": "ignored",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.data
        self.assertEqual(payload["deterministic_progression"]["completed_slots"], [1, 2, 3])

    @patch("project_middle_layer.api.views.dispatch_calculus_timeline_runtime_events")
    def test_calculus_timeline_post_dispatches_runtime_events(self, mock_dispatch):
        url = reverse("project_middle_layer:project-middle-layer-calculus-timeline-runtime")
        response = self.client.post(
            url,
            {
                "selected_slot": 2,
                "completed_slots": [1],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_dispatch.assert_called_once()


class ProjectMiddleLayerCalculusTimelineRuntimeSignalTests(SimpleTestCase):
    def test_all_16_slots_emit_required_signal_blocks(self):
        payload = build_calculus_timeline_runtime_payload(selected_slot=1)

        self.assertEqual(payload["mode"], "calculus_temporal_timeline_runtime")
        self.assertEqual(payload["timeline"]["slot_count"], 16)
        self.assertEqual(len(payload["slots"]), 16)

        slot_indexes = sorted(int(slot["slot_index"]) for slot in payload["slots"])
        self.assertEqual(slot_indexes, list(range(1, 17)))

        for slot in payload["slots"]:
            self.assertIn("calculus_operation", slot)
            self.assertIn(slot["calculus_operation"], ["Integral", "Continuity", "Limit", "Derivative"])
            self.assertIn("temporal_alignment", slot)
            self.assertIn(slot["temporal_alignment"], ["past", "present-past", "present-future", "future"])
            self.assertIn("gate", slot)
            self.assertIn("locked", slot["gate"])
            self.assertIn("state", slot)
            self.assertIn("drift_score", slot["state"])
            self.assertIn("stability_score", slot["state"])
            self.assertIn("alignment_score", slot["state"])
            self.assertIn("semantic_tags", slot["state"])
            self.assertIn("micro_signals", slot["state"])
            self.assertIn("industry_metadata", slot)
            self.assertIn("sector_name", slot["industry_metadata"])
            self.assertIn("group_name", slot["industry_metadata"])
            self.assertIn("industry", slot["industry_metadata"])
            self.assertIn("sub_industry", slot["industry_metadata"])
            self.assertIn("event", slot)
            self.assertEqual(slot["event"]["event_type"], "middle_layer.timeline.slot_state")

    def test_drift_alignment_is_deterministic_for_matching_and_mismatched_content(self):
        matched = build_calculus_timeline_runtime_payload(
            selected_slot=1,
            slot_content={
                "1": "history integrate foundation context archive",
            },
        )
        mismatched = build_calculus_timeline_runtime_payload(
            selected_slot=1,
            slot_content={
                "1": "future optimize forecast trajectory derivative",
            },
        )

        matched_slot = matched["selected_slot_state"]
        mismatched_slot = mismatched["selected_slot_state"]

        self.assertGreater(matched_slot["state"]["alignment_score"], mismatched_slot["state"]["alignment_score"])
        self.assertLess(matched_slot["state"]["drift_score"], mismatched_slot["state"]["drift_score"])

    def test_industry_context_overrides_are_propagated_to_slot_payload_and_scoring(self):
        payload = build_calculus_timeline_runtime_payload(
            selected_slot=2,
            slot_content={
                "2": "software cloud architecture enterprise language systems",
            },
            industry_context={
                "group": "Language",
                "industry": "Software",
                "sub_industry": "Enterprise Operating System Architecture",
            },
        )

        slot = payload["selected_slot_state"]
        self.assertEqual(slot["industry_metadata"]["group_name"], "Language")
        self.assertEqual(slot["industry_metadata"]["industry"], "Software")
        self.assertEqual(slot["industry_metadata"]["sub_industry"], "Enterprise Operating System Architecture")
        self.assertTrue(any(tag.startswith("industry:") for tag in slot["state"]["semantic_tags"]))

    def test_phase_gating_is_strictly_enforced(self):
        locked_payload = build_calculus_timeline_runtime_payload(selected_slot=8, completed_slots=[1, 2, 3])
        unlocked_payload = build_calculus_timeline_runtime_payload(selected_slot=8, completed_slots=[1, 2, 3, 4])

        self.assertTrue(locked_payload["selected_slot_state"]["gate"]["locked"])
        self.assertFalse(unlocked_payload["selected_slot_state"]["gate"]["locked"])

    def test_repeated_calls_are_deterministic_for_same_inputs(self):
        input_payload = {
            "selected_slot": 4,
            "completed_slots": [1, 2],
            "slot_content": {"4": "future threshold readiness gate limit"},
            "industry_context": {
                "group": "Science",
                "industry": "Biotechnology",
            },
        }
        first = build_calculus_timeline_runtime_payload(**input_payload)
        second = build_calculus_timeline_runtime_payload(**input_payload)
        self.assertEqual(first, second)

    def test_slot_event_envelope_has_governed_contract_fields(self):
        payload = build_calculus_timeline_runtime_payload(selected_slot=3)
        slot_event = payload["selected_slot_state"]["event"]

        self.assertEqual(slot_event["event_type"], "middle_layer.timeline.slot_state")
        self.assertEqual(slot_event["event_version"], "v1")
        self.assertEqual(slot_event["source"], "project_middle_layer.calculus_timeline_runtime")
        self.assertIn("gate_locked", slot_event)
        self.assertIn("drift_score", slot_event)
        self.assertIn("alignment_score", slot_event)

    def test_slot_state_changed_events_include_contract_metadata(self):
        payload = build_calculus_timeline_runtime_payload(
            selected_slot=2,
            prior_slot_states={
                "2": {
                    "drift_score": 0.95,
                    "alignment_score": 0.05,
                    "gate_locked": True,
                    "completed": True,
                }
            },
            completed_slots=[],
        )
        changed = [item for item in payload["events"] if item.get("slot_index") == 2]
        self.assertTrue(len(changed) > 0)
        self.assertEqual(changed[0]["event_type"], "middle_layer.timeline.slot_state_changed")
        self.assertEqual(changed[0]["event_version"], "v1")
        self.assertEqual(changed[0]["source"], "project_middle_layer.calculus_timeline_runtime")
        self.assertIn("gate_locked", changed[0])
        self.assertIn("slot_completed", changed[0])
        self.assertIn("stability_score", changed[0])
        self.assertIn("industry_metadata", changed[0])
        self.assertIn("semantic_state", changed[0])
        self.assertIn("completed_slots", changed[0])


class ProjectMiddleLayerTimelineOrchestrationDispatchTests(SimpleTestCase):
    @patch("project_middle_layer.services.dispatch_semantic_webhook_event")
    def test_dispatch_emits_orchestration_events_from_selected_slot(self, mock_dispatch):
        payload = build_calculus_timeline_runtime_payload(
            selected_slot=4,
            completed_slots=[1, 2, 3, 4],
            slot_content={
                "4": "misaligned noisy drift with unstable context",
            },
            prior_slot_states={
                "4": {
                    "alignment_score": 0.9,
                    "gate_locked": True,
                    "completed": False,
                }
            },
        )

        dispatch_count = dispatch_calculus_timeline_runtime_events(payload)

        self.assertGreaterEqual(dispatch_count, 4)
        dispatched_event_types = [call.kwargs.get("event_type") for call in mock_dispatch.call_args_list]
        self.assertIn("middle_layer.timeline.slot_state", dispatched_event_types)
        self.assertIn("middle_layer.timeline.slot_completion", dispatched_event_types)
        self.assertIn("middle_layer.timeline.drift_threshold", dispatched_event_types)
        self.assertIn("middle_layer.timeline.alignment_shift", dispatched_event_types)
        self.assertIn("middle_layer.timeline.gate_unlock", dispatched_event_types)

        first_payload = mock_dispatch.call_args_list[0].kwargs.get("payload", {})
        self.assertEqual(first_payload.get("priority_order"), ["critical", "warn", "info"])
        queue = first_payload.get("orchestration_priority_queue", [])
        self.assertTrue(len(queue) > 0)
        self.assertIn(queue[0].get("priority"), ["critical", "warn", "info"])
        platform_intelligence = first_payload.get("platform_intelligence", {})
        self.assertEqual(platform_intelligence.get("orchestration", {}).get("priority_order"), ["critical", "warn", "info"])
        self.assertEqual(platform_intelligence.get("orchestration", {}).get("trigger_count"), len(queue))
        self.assertIn(platform_intelligence.get("synthesis", {}).get("risk_level"), ["high", "medium", "low"])
        self.assertIn("drift_score", platform_intelligence.get("semantic_metadata", {}))
        self.assertIn("alignment_score", platform_intelligence.get("semantic_metadata", {}))
        self.assertEqual(platform_intelligence.get("lfo_engine", {}).get("mode"), "lfo_expansion_v1")
        self.assertEqual(platform_intelligence.get("lfo_engine", {}).get("group_template_count"), 16)
        self.assertEqual(platform_intelligence.get("lfo_engine", {}).get("industry_template_count"), 64)
        self.assertEqual(platform_intelligence.get("lfo_engine", {}).get("science_lens_count"), 4)
        self.assertEqual(
            platform_intelligence.get("lfo_engine", {}).get("surface_modes", {}).get("science"),
            "mbsp_consumer_gui_surface",
        )

        priority_rank = {"critical": 0, "warn": 1, "info": 2}
        ranked = [priority_rank.get(item.get("priority"), 3) for item in queue]
        self.assertEqual(ranked, sorted(ranked))

    @patch("project_middle_layer.services.dispatch_semantic_webhook_event")
    def test_dispatch_derives_no_gate_unlock_when_phase_stays_locked(self, mock_dispatch):
        payload = build_calculus_timeline_runtime_payload(
            selected_slot=8,
            completed_slots=[1, 2, 3, 4, 5, 6, 7],
            slot_content={
                "8": "future optimize forecast trajectory derivative",
            },
            prior_slot_states={
                "8": {
                    "alignment_score": 0.7,
                    "gate_locked": False,
                    "completed": False,
                }
            },
        )

        dispatch_calculus_timeline_runtime_events(payload)
        gate_unlock_calls = [
            call
            for call in mock_dispatch.call_args_list
            if call.kwargs.get("event_type") == "middle_layer.timeline.gate_unlock"
        ]
        gate_unlock_slot_indexes = [
            call.kwargs.get("payload", {}).get("timeline_event", {}).get("slot_index")
            for call in gate_unlock_calls
        ]
        self.assertNotIn(8, gate_unlock_slot_indexes)

    @patch("project_middle_layer.services.dispatch_semantic_webhook_event")
    def test_dispatch_prioritizes_critical_before_warn_and_info(self, mock_dispatch):
        payload = {
            "mode": "calculus_temporal_timeline_runtime",
            "deterministic_progression": {
                "completed_slots": [1, 2, 3, 4],
                "phase_gates": [
                    {"phase": "Ideas", "locked": False},
                    {"phase": "Seeds", "locked": False},
                    {"phase": "Projects", "locked": True},
                    {"phase": "MVP", "locked": True},
                ],
            },
            "selected_slot_state": {
                "event": {
                    "event_type": "middle_layer.timeline.slot_state",
                    "slot_index": 4,
                    "phase": "Ideas",
                    "slot_completed": True,
                    "gate_locked": False,
                    "drift_score": 0.9,
                    "alignment_score": 0.3,
                    "semantic_state": {
                        "drift_score": 0.9,
                        "alignment_score": 0.3,
                    },
                }
            },
            "events": [],
        }

        dispatch_calculus_timeline_runtime_events(payload)
        queue = mock_dispatch.call_args_list[0].kwargs.get("payload", {}).get("orchestration_priority_queue", [])

        self.assertGreaterEqual(len(queue), 4)
        priority_rank = {"critical": 0, "warn": 1, "info": 2}
        ranked = [priority_rank.get(item.get("priority"), 3) for item in queue]
        self.assertEqual(ranked, sorted(ranked))

        event_types = [item.get("event_type") for item in queue]
        self.assertIn("middle_layer.timeline.drift_threshold", event_types)
        self.assertIn("middle_layer.timeline.alignment_shift", event_types)
        self.assertIn("middle_layer.timeline.slot_completion", event_types)
        self.assertIn("middle_layer.timeline.gate_unlock", event_types)


class ProjectMiddleLayerTimelineWebhookEnvelopeTests(TestCase):
    @patch("project_middle_layer.webhooks.urllib_request.urlopen")
    def test_dispatch_normalizes_timeline_event_payload_for_listeners(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"ok"
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        webhook = SemanticWebhook.objects.create(
            name="Timeline Runtime Webhook",
            target_url="https://example.com/timeline-webhook",
            event_type="middle_layer.timeline.slot_state_changed",
            status="active",
        )

        dispatch_semantic_webhook_event(
            event_type="middle_layer.timeline.slot_state_changed",
            payload={
                "mode": "calculus_temporal_timeline_runtime",
                "completed_slots": [1, 2, 3, 4],
                "timeline_event": {
                    "event_type": "middle_layer.timeline.slot_state_changed",
                    "slot_index": 5,
                    "phase": "Seeds",
                    "locked": True,
                    "completed": False,
                    "drift_score": 0.44,
                    "alignment_score": 0.56,
                },
            },
        )

        delivery = SemanticWebhookDelivery.objects.filter(webhook=webhook).latest("created_at")
        event_payload = delivery.payload.get("timeline_event", {})
        self.assertEqual(event_payload.get("event_type"), "middle_layer.timeline.slot_state_changed")
        self.assertEqual(event_payload.get("slot_index"), 5)
        self.assertTrue(event_payload.get("gate_locked"))
        self.assertFalse(event_payload.get("slot_completed"))
        self.assertEqual(event_payload.get("priority"), "info")
        self.assertEqual(event_payload.get("completed_slots"), [1, 2, 3, 4])
        platform_intelligence = delivery.payload.get("platform_intelligence", {})
        self.assertEqual(platform_intelligence.get("orchestration", {}).get("priority_order"), ["critical", "warn", "info"])
        self.assertEqual(platform_intelligence.get("slot_progression", {}).get("completed_count"), 4)
        self.assertIn(platform_intelligence.get("synthesis", {}).get("risk_level"), ["high", "medium", "low"])

    @patch("project_middle_layer.webhooks.urllib_request.urlopen")
    def test_dispatch_routes_to_matching_subscribers_only_across_event_types(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"ok"
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        slot_state_hook = SemanticWebhook.objects.create(
            name="Timeline Slot State Hook",
            target_url="https://example.com/timeline-slot-state",
            event_type="middle_layer.timeline.slot_state",
            status="active",
        )
        slot_changed_hook = SemanticWebhook.objects.create(
            name="Timeline Slot Changed Hook",
            target_url="https://example.com/timeline-slot-changed",
            event_type="middle_layer.timeline.slot_state_changed",
            status="active",
        )
        pipeline_hook = SemanticWebhook.objects.create(
            name="Pipeline Hook",
            target_url="https://example.com/pipeline",
            event_type="pipeline.completed",
            status="active",
        )

        dispatch_semantic_webhook_event(
            event_type="middle_layer.timeline.slot_state_changed",
            payload={
                "timeline_event": {
                    "event_type": "middle_layer.timeline.slot_state_changed",
                    "slot_index": 6,
                    "phase": "Seeds",
                    "locked": False,
                    "completed": True,
                },
                "completed_slots": [1, 2, 3, 4, 5, 6],
            },
        )

        self.assertEqual(
            SemanticWebhookDelivery.objects.filter(webhook=slot_state_hook).count(),
            0,
        )
        self.assertEqual(
            SemanticWebhookDelivery.objects.filter(webhook=pipeline_hook).count(),
            0,
        )
        delivery = SemanticWebhookDelivery.objects.filter(webhook=slot_changed_hook).latest("created_at")
        event_payload = delivery.payload.get("timeline_event", {})
        self.assertFalse(event_payload.get("gate_locked"))
        self.assertTrue(event_payload.get("slot_completed"))

    @patch("project_middle_layer.webhooks.urllib_request.urlopen")
    def test_dispatch_routes_derived_orchestration_event_to_matching_listener(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"ok"
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        completion_hook = SemanticWebhook.objects.create(
            name="Timeline Completion Hook",
            target_url="https://example.com/timeline-completion",
            event_type="middle_layer.timeline.slot_completion",
            status="active",
        )
        changed_hook = SemanticWebhook.objects.create(
            name="Timeline Slot Changed Hook",
            target_url="https://example.com/timeline-slot-changed",
            event_type="middle_layer.timeline.slot_state_changed",
            status="active",
        )

        dispatch_semantic_webhook_event(
            event_type="middle_layer.timeline.slot_completion",
            payload={
                "timeline_event": {
                    "event_type": "middle_layer.timeline.slot_completion",
                    "slot_index": 4,
                    "phase": "Ideas",
                    "locked": False,
                    "completed": True,
                    "drift_score": 0.77,
                    "alignment_score": 0.3,
                },
                "completed_slots": [1, 2, 3, 4],
            },
        )

        self.assertEqual(SemanticWebhookDelivery.objects.filter(webhook=changed_hook).count(), 0)
        delivery = SemanticWebhookDelivery.objects.filter(webhook=completion_hook).latest("created_at")
        event_payload = delivery.payload.get("timeline_event", {})
        self.assertEqual(event_payload.get("event_type"), "middle_layer.timeline.slot_completion")
        self.assertEqual(event_payload.get("slot_index"), 4)
        self.assertTrue(event_payload.get("slot_completed"))
        self.assertEqual(event_payload.get("priority"), "info")

    @patch("project_middle_layer.webhooks.urllib_request.urlopen")
    def test_retry_webhook_delivery_sends_normalized_timeline_payload(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"ok"
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        webhook = SemanticWebhook.objects.create(
            name="Timeline Retry Hook",
            target_url="https://example.com/retry-hook",
            event_type="middle_layer.timeline.slot_state_changed",
            status="active",
        )

        delivery = SemanticWebhookDelivery.objects.create(
            webhook=webhook,
            event_type="middle_layer.timeline.slot_state_changed",
            payload={
                "timeline_event": {
                    "event_type": "middle_layer.timeline.slot_state_changed",
                    "slot_index": 7,
                    "phase": "Seeds",
                    "locked": True,
                    "completed": False,
                },
                "completed_slots": [1, 2, 3, 4, 5, 6],
            },
            status="failed",
        )

        retried = retry_webhook_delivery(delivery)
        self.assertEqual(retried.status, "delivered")

        request_obj = mock_urlopen.call_args[0][0]
        payload = json.loads(request_obj.data.decode("utf-8"))
        timeline_event = payload.get("timeline_event", {})
        self.assertTrue(timeline_event.get("gate_locked"))
        self.assertFalse(timeline_event.get("slot_completed"))
        self.assertEqual(timeline_event.get("priority"), "info")
        self.assertEqual(timeline_event.get("completed_slots"), [1, 2, 3, 4, 5, 6])
        platform_intelligence = payload.get("platform_intelligence", {})
        self.assertEqual(platform_intelligence.get("orchestration", {}).get("priority_order"), ["critical", "warn", "info"])
        self.assertEqual(platform_intelligence.get("slot_progression", {}).get("completed_count"), 6)

    @patch("project_middle_layer.webhooks.urllib_request.urlopen")
    def test_retry_webhook_delivery_normalizes_priority_queue_order(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"ok"
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        webhook = SemanticWebhook.objects.create(
            name="Timeline Priority Retry Hook",
            target_url="https://example.com/retry-priority-hook",
            event_type="middle_layer.timeline.slot_state_changed",
            status="active",
        )

        delivery = SemanticWebhookDelivery.objects.create(
            webhook=webhook,
            event_type="middle_layer.timeline.slot_state_changed",
            payload={
                "timeline_event": {
                    "event_type": "middle_layer.timeline.slot_state_changed",
                    "slot_index": 7,
                    "phase": "Seeds",
                    "locked": True,
                    "completed": False,
                },
                "orchestration_priority_queue": [
                    {"queue_index": 2, "event_type": "middle_layer.timeline.slot_completion", "slot_index": 4, "priority": "info"},
                    {"queue_index": 0, "event_type": "middle_layer.timeline.drift_threshold", "slot_index": 4, "priority": "critical"},
                    {"queue_index": 1, "event_type": "middle_layer.timeline.alignment_shift", "slot_index": 4, "priority": "warn"},
                ],
            },
            status="failed",
        )

        retried = retry_webhook_delivery(delivery)
        self.assertEqual(retried.status, "delivered")

        request_obj = mock_urlopen.call_args[0][0]
        payload = json.loads(request_obj.data.decode("utf-8"))
        queue = payload.get("orchestration_priority_queue", [])
        self.assertEqual([item.get("priority") for item in queue], ["critical", "warn", "info"])
        platform_intelligence = payload.get("platform_intelligence", {})
        self.assertEqual(platform_intelligence.get("orchestration", {}).get("trigger_count"), 3)
        self.assertEqual(platform_intelligence.get("orchestration", {}).get("highest_priority"), "critical")


class ProjectMiddleLayerLfoEngineTests(APITestCase):
    def test_lfo_engine_generates_16_group_and_64_industry_templates(self):
        catalog = load_macro_industry_groups()
        group_templates = build_sevm_group_templates(
            group_catalog=catalog,
            timeline_snapshot={
                "latest_slot_index": 8,
                "latest_phase": "Seeds",
                "drift_score": 0.2,
                "stability_score": 0.8,
                "alignment_score": 0.8,
                "completion_ratio": 0.5,
            },
            synthesis_snapshot={
                "risk_level": "low",
                "drift_trend": "stable",
                "alignment_trajectory": "improving",
            },
        )
        industry_templates = build_industry_lfo_templates(group_templates)

        self.assertEqual(len(group_templates), 16)
        self.assertEqual(len(industry_templates), 64)
        self.assertTrue(all(item.get("sevm_template", {}).get("logical_branch_count") == 16 for item in group_templates))
        self.assertEqual(
            sorted(int(item.get("group_metadata", {}).get("group_id") or 0) for item in group_templates),
            list(range(1, 17)),
        )
        self.assertTrue(all(str(item.get("inherits_from") or "").startswith("group_lfo_") for item in industry_templates))
        self.assertTrue(all(len(item.get("branch_ids", [])) == 16 for item in industry_templates))
        self.assertEqual(len(industry_templates), 64)
        self.assertTrue(all(item.get("sevm_template", {}).get("logical_branch_count") == 16 for item in group_templates))
        self.assertEqual(
            sorted(int(item.get("group_metadata", {}).get("group_id") or 0) for item in group_templates),
            list(range(1, 17)),
        )
        self.assertTrue(all(str(item.get("inherits_from") or "").startswith("group_lfo_") for item in industry_templates))
        self.assertTrue(all(len(item.get("branch_ids", [])) == 16 for item in industry_templates))

    def test_feature_probability_pipeline_is_deterministic(self):
        first = evaluate_feature_probability(
            feature_name="mvp_ui_synthesis",
            timeline_snapshot={
                "drift_score": 0.2,
                "alignment_score": 0.82,
                "completion_ratio": 0.5,
            },
            synthesis_snapshot={"risk_level": "medium"},
        )
        second = evaluate_feature_probability(
            feature_name="mvp_ui_synthesis",
            timeline_snapshot={
                "drift_score": 0.2,
                "alignment_score": 0.82,
                "completion_ratio": 0.5,
            },
            synthesis_snapshot={"risk_level": "medium"},
        )

        self.assertEqual(first, second)
        self.assertIn(first.get("grade"), ["A", "B", "C"])
        self.assertIn("statistics", first.get("pipeline", {}))
        self.assertIn("algebra", first.get("pipeline", {}))
        self.assertIn("calculus", first.get("pipeline", {}))
        self.assertIn("probability", first.get("pipeline", {}))

    def test_lfo_engine_api_returns_four_surface_contract(self):
        url = reverse("project_middle_layer:project-middle-layer-lfo-engine")
        response = self.client.post(
            url,
            {
                "timeline_snapshot": {
                    "latest_slot_index": 12,
                    "latest_phase": "Projects",
                    "drift_score": 0.31,
                    "stability_score": 0.72,
                    "alignment_score": 0.69,
                    "completion_ratio": 0.75,
                },
                "synthesis_snapshot": {
                    "risk_level": "medium",
                    "drift_trend": "rising",
                    "alignment_trajectory": "stable",
                },
                "trigger_count": 2,
                "feature_pathways": ["project_to_mvp_slot_12", "consumer_gui_science_surface"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.data
        self.assertEqual(payload.get("mode"), "lfo_expansion_v1")
        self.assertEqual(payload.get("template_summary", {}).get("group_template_count"), 16)
        self.assertEqual(payload.get("template_summary", {}).get("industry_template_count"), 64)
        self.assertEqual(len(payload.get("sevm_logical_branches", [])), 16)
        self.assertGreaterEqual(len(payload.get("feature_probability", [])), 2)
        self.assertEqual(payload.get("math_surface", {}).get("mode"), "sacp_probability_surface")
        self.assertEqual(payload.get("language_surface", {}).get("mode"), "ednp_transcript_surface")
        self.assertEqual(payload.get("arts_surface", {}).get("mode"), "vlsm_creator_surface")
        self.assertEqual(payload.get("science_surface", {}).get("mode"), "mbsp_consumer_gui_surface")
        self.assertEqual(len(payload.get("language_surface", {}).get("documents", [])), 4)
        self.assertEqual(len(payload.get("arts_surface", {}).get("creator_scaffolds", [])), 16)
        self.assertEqual(len(payload.get("science_surface", {}).get("lenses", [])), 4)
        self.assertEqual(len(payload.get("industry_templates", [])), 64)
        self.assertTrue(all("surface_contract" in item for item in payload.get("industry_templates", [])))
        self.assertTrue(all("timeline_binding" in item for item in payload.get("industry_templates", [])))
        self.assertTrue(all("sevm_branch_lineage" in item for item in payload.get("industry_templates", [])))
        self.assertTrue(all(item.get("inheritance", {}).get("override_allowed") is False for item in payload.get("industry_templates", [])))
        self.assertTrue(all(len(item.get("surface_contract", {}).get("science", {}).get("lenses", [])) == 4 for item in payload.get("industry_templates", [])))
        interaction_models = {
            str(item.get("interaction_model") or "")
            for item in payload.get("science_surface", {}).get("lenses", [])
        }
        self.assertEqual(
            interaction_models,
            {
                "deterministic_behavior",
                "organic_interaction_flow",
                "collaborative_community_patterns",
                "deployment_visual_physics",
            },
        )

    def test_mbsp_science_gui_surface_binds_timeline_orchestration_and_unified_metadata(self):
        surface = build_consumer_gui_science_surface(
            timeline_snapshot={
                "latest_slot_index": 12,
                "latest_phase": "Projects",
                "drift_score": 0.22,
                "stability_score": 0.81,
                "alignment_score": 0.79,
                "completion_ratio": 0.75,
            },
            synthesis_snapshot={
                "risk_level": "medium",
                "drift_trend": "rising",
                "alignment_trajectory": "improving",
            },
            trigger_count=3,
        )

        self.assertEqual(surface.get("mode"), "mbsp_consumer_gui_surface")
        self.assertEqual(surface.get("latest_phase"), "projects")
        self.assertEqual(surface.get("trigger_count"), 3)
        self.assertEqual(len(surface.get("lenses", [])), 4)
        self.assertTrue(all(item.get("binds_to_timeline") for item in surface.get("lenses", [])))
        self.assertTrue(all(item.get("binds_to_orchestration") for item in surface.get("lenses", [])))
        self.assertTrue(all(item.get("binds_to_unified_intelligence") for item in surface.get("lenses", [])))
        self.assertTrue(all("timeline_progression" in item for item in surface.get("lenses", [])))
        self.assertTrue(all("orchestration" in item for item in surface.get("lenses", [])))
        self.assertTrue(all("unified_intelligence" in item for item in surface.get("lenses", [])))
        self.assertTrue(all("surface_tiers" in item for item in surface.get("lenses", [])))

    def test_mbsp_science_gui_surface_emits_studio_and_enterprise_post_mvp_states(self):
        studio_surface = build_consumer_gui_science_surface(
            timeline_snapshot={
                "latest_slot_index": 16,
                "latest_phase": "MVP",
                "drift_score": 0.26,
                "stability_score": 0.7,
                "alignment_score": 0.72,
                "completion_ratio": 1.0,
            },
            synthesis_snapshot={
                "risk_level": "medium",
                "drift_trend": "stable",
                "alignment_trajectory": "improving",
            },
            trigger_count=4,
        )
        enterprise_surface = build_consumer_gui_science_surface(
            timeline_snapshot={
                "latest_slot_index": 16,
                "latest_phase": "MVP",
                "drift_score": 0.12,
                "stability_score": 0.84,
                "alignment_score": 0.88,
                "completion_ratio": 1.0,
            },
            synthesis_snapshot={
                "risk_level": "low",
                "drift_trend": "falling",
                "alignment_trajectory": "improving",
            },
            trigger_count=1,
        )

        self.assertEqual(studio_surface.get("surface_phase"), "studio")
        self.assertTrue(studio_surface.get("surface_tiers", {}).get("studio", {}).get("active"))
        self.assertFalse(studio_surface.get("surface_tiers", {}).get("enterprise", {}).get("active"))
        self.assertEqual(enterprise_surface.get("surface_phase"), "enterprise")
        self.assertTrue(enterprise_surface.get("surface_tiers", {}).get("enterprise", {}).get("active"))
        self.assertTrue(enterprise_surface.get("surface_tiers", {}).get("studio", {}).get("unlocked"))

    def test_lfo_engine_envelope_builder_outputs_full_contract(self):
        payload = build_lfo_engine_envelope(
            timeline_snapshot={
                "latest_slot_index": 10,
                "latest_phase": "Projects",
                "drift_score": 0.34,
                "stability_score": 0.71,
                "alignment_score": 0.66,
                "completion_ratio": 0.625,
            },
            synthesis_snapshot={
                "risk_level": "medium",
                "drift_trend": "rising",
                "alignment_trajectory": "declining",
            },
            trigger_count=3,
            feature_pathways=["timeline_gate_progression"],
        )
        self.assertEqual(payload.get("mode"), "lfo_expansion_v1")
        self.assertEqual(payload.get("template_summary", {}).get("group_template_count"), 16)
        self.assertEqual(payload.get("template_summary", {}).get("industry_template_count"), 64)
        self.assertEqual(len(payload.get("sevm_logical_branches", [])), 16)
        self.assertEqual(payload.get("math_surface", {}).get("mode"), "sacp_probability_surface")
        self.assertEqual(payload.get("language_surface", {}).get("mode"), "ednp_transcript_surface")
        self.assertEqual(payload.get("arts_surface", {}).get("mode"), "vlsm_creator_surface")
        self.assertEqual(payload.get("science_surface", {}).get("mode"), "mbsp_consumer_gui_surface")
        self.assertEqual(len(payload.get("industry_templates", [])), 64)

    def test_micro_templates_generate_256_rows_with_inherited_surfaces(self):
        payload = build_lfo_engine_envelope(
            timeline_snapshot={
                "latest_slot_index": 12,
                "latest_phase": "Projects",
                "drift_score": 0.28,
                "stability_score": 0.76,
                "alignment_score": 0.74,
                "completion_ratio": 0.75,
            },
            synthesis_snapshot={
                "risk_level": "medium",
                "drift_trend": "rising",
                "alignment_trajectory": "improving",
            },
            trigger_count=2,
        )
        micro_templates = payload.get("micro_templates", [])

        self.assertEqual(len(micro_templates), 256)
        self.assertEqual(payload.get("micro_template_summary", {}).get("micro_template_count"), 256)
        self.assertTrue(all(str(item.get("inherits_from") or "").startswith("industry_lfo_") for item in micro_templates))
        self.assertTrue(all(item.get("inheritance", {}).get("override_allowed") is False for item in micro_templates))
        self.assertTrue(all(len(item.get("surface_contract", {}).get("math", {}).get("feature_rows", [])) == 1 for item in micro_templates))
        self.assertTrue(all(len(item.get("surface_contract", {}).get("language", {}).get("documents", [])) == 4 for item in micro_templates))
        self.assertTrue(all(len(item.get("surface_contract", {}).get("science", {}).get("lenses", [])) == 4 for item in micro_templates))
        self.assertTrue(all(item.get("surface_contract", {}).get("math", {}).get("mode") == "sacp_probability_surface" for item in micro_templates))
        self.assertTrue(all(item.get("surface_contract", {}).get("science", {}).get("mode") == "mbsp_consumer_gui_surface" for item in micro_templates))

    def test_micro_template_generation_is_deterministically_inherited_from_industry(self):
        group_templates = build_sevm_group_templates(
            group_catalog=load_macro_industry_groups(),
            timeline_snapshot={"latest_slot_index": 8, "drift_score": 0.2, "alignment_score": 0.8},
            synthesis_snapshot={"risk_level": "medium", "drift_trend": "stable", "alignment_trajectory": "stable"},
        )
        industry_templates = build_industry_lfo_templates(group_templates)
        micro_templates = build_micro_lfo_templates(industry_templates)

        self.assertEqual(len(micro_templates), 256)
        self.assertTrue(all(str(item.get("inherits_from") or "").startswith("industry_lfo_") for item in micro_templates))
        self.assertTrue(all(len(item.get("branch_ids", [])) == 16 for item in micro_templates))
        self.assertTrue(all(len(item.get("surface_contract", {}).get("science", {}).get("lenses", [])) == 4 for item in micro_templates))
        self.assertTrue(all(item.get("inheritance", {}).get("override_allowed") is False for item in micro_templates))
        self.assertTrue(
            all(
                lens.get("unified_intelligence", {}).get("drift_trend") == "stable"
                and lens.get("unified_intelligence", {}).get("alignment_trajectory") == "stable"
                for item in micro_templates
                for lens in item.get("surface_contract", {}).get("science", {}).get("lenses", [])
            )
        )

    def test_industry_template_inheritance_matrix_is_stable(self):
        payload = build_lfo_engine_envelope(
            timeline_snapshot={
                "latest_slot_index": 8,
                "latest_phase": "Seeds",
                "drift_score": 0.22,
                "stability_score": 0.79,
                "alignment_score": 0.77,
                "completion_ratio": 0.5,
            },
            synthesis_snapshot={
                "risk_level": "medium",
                "drift_trend": "rising",
                "alignment_trajectory": "improving",
            },
            trigger_count=1,
        )
        templates = payload.get("industry_templates", [])
        first = templates[0]
        self.assertEqual(first.get("mode") if isinstance(first, dict) else None, None)
        self.assertTrue(first.get("template_id", "").startswith("industry_lfo_"))
        self.assertTrue(first.get("inherits_from", "").startswith("group_lfo_"))
        self.assertEqual(first.get("surface_contract", {}).get("math", {}).get("mode"), "sacp_probability_surface")
        self.assertEqual(first.get("surface_contract", {}).get("language", {}).get("mode"), "ednp_transcript_surface")
        self.assertEqual(first.get("surface_contract", {}).get("arts", {}).get("mode"), "vlsm_creator_surface")
        self.assertEqual(first.get("surface_contract", {}).get("science", {}).get("mode"), "mbsp_consumer_gui_surface")
        self.assertEqual(len(first.get("surface_contract", {}).get("science", {}).get("lenses", [])), 4)
        self.assertFalse(first.get("inheritance", {}).get("override_allowed"))


class ProjectMiddleLayerWizardAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="wizard@example.com",
            username="wizard",
            name="Wizard User",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

    def _grant_capabilities(self, user, capabilities):
        role = SemanticRole.objects.create(
            name=f"Role {SemanticRole.objects.count() + 1}",
            slug=f"role-{SemanticRole.objects.count() + 1}",
            capabilities=list(capabilities),
        )
        SemanticUserProfile.objects.update_or_create(
            user=user,
            defaults={"default_role": role},
        )
        return role

    def test_wizard_end_to_end_creates_or_updates_project_node(self):
        start_url = reverse("project_middle_layer:project-middle-layer-wizard-start")
        start_response = self.client.post(
            start_url,
            {
                "slug": "phase3-wizard-project",
                "name": "Phase3 Wizard Project",
                "semantic_intent": "ExpandAndIntegrate",
                "mlas_tier": "Semantic Utility",
                "btif_classification": "ExpansionFlow",
            },
            format="json",
        )
        self.assertEqual(start_response.status_code, status.HTTP_201_CREATED)
        wizard_id = start_response.data["wizard_id"]

        tags_url = reverse(
            "project_middle_layer:project-middle-layer-wizard-tags",
            kwargs={"wizard_id": wizard_id},
        )
        tags_response = self.client.post(
            tags_url,
            {
                "semantic_tags": ["project", "wizard", "phase3"],
                "metadata": {"source": "api-wizard-test"},
            },
            format="json",
        )
        self.assertEqual(tags_response.status_code, status.HTTP_200_OK)

        compile_url = reverse(
            "project_middle_layer:project-middle-layer-wizard-compile",
            kwargs={"wizard_id": wizard_id},
        )
        compile_response = self.client.post(compile_url, {}, format="json")
        self.assertEqual(compile_response.status_code, status.HTTP_200_OK)
        self.assertIn("schema", compile_response.data)
        self.assertIn("drift_forecast", compile_response.data)
        self.assertIn("identity_payload", compile_response.data)
        self.assertIn("branch_resolution", compile_response.data["identity_payload"]["identity"])
        self.assertIn("specialized_path", compile_response.data)
        self.assertEqual(compile_response.data["specialized_path"]["compile_status"], "ready")

        node = ProjectNode.objects.get(slug="phase3-wizard-project")
        self.assertEqual(node.name, "Phase3 Wizard Project")
        self.assertEqual(node.metadata.get("source"), "api-wizard-test")

    def test_wizard_accepts_short_alias_payloads(self):
        start_url = reverse("project_middle_layer:project-middle-layer-wizard-start")
        start_response = self.client.post(
            start_url,
            {
                "title": "Neighborhood Story Lab",
                "intent": "community_program",
                "tier": "public",
                "description": "A grassroots storytelling hub for local residents.",
            },
            format="json",
        )
        self.assertEqual(start_response.status_code, status.HTTP_201_CREATED)
        wizard_id = start_response.data["wizard_id"]

        tags_url = reverse(
            "project_middle_layer:project-middle-layer-wizard-tags",
            kwargs={"wizard_id": wizard_id},
        )
        tags_response = self.client.post(
            tags_url,
            {
                "tags": ["storytelling", "community", "workshops", "local-media"],
            },
            format="json",
        )
        self.assertEqual(tags_response.status_code, status.HTTP_200_OK)

        compile_url = reverse(
            "project_middle_layer:project-middle-layer-wizard-compile",
            kwargs={"wizard_id": wizard_id},
        )
        compile_response = self.client.post(compile_url, {}, format="json")
        self.assertEqual(compile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(compile_response.data["schema"]["name"], "Neighborhood Story Lab")
        self.assertIn("storytelling", compile_response.data["schema"]["semantic_tags"])

        node = ProjectNode.objects.get(slug="neighborhood-story-lab")
        self.assertEqual(node.name, "Neighborhood Story Lab")
        self.assertEqual(node.metadata.get("visibility_tier"), "public")

    def test_batch_compile_endpoint_compiles_multiple_payloads(self):
        url = reverse("project_middle_layer:project-middle-layer-compile-batch")
        response = self.client.post(
            url,
            {
                "projects": [
                    {
                        "title": "Batch Project One",
                        "intent": "community_program",
                        "tier": "public",
                        "tags": ["storytelling", "community"],
                    },
                    {
                        "title": "Batch Project Two",
                        "intent": "education_flow",
                        "tier": "public",
                        "tags": ["learning", "community"],
                    },
                ],
                "atomic": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"]["requested"], 2)
        self.assertEqual(response.data["summary"]["compiled"], 2)
        self.assertEqual(response.data["summary"]["failed"], 0)
        self.assertEqual(ProjectNode.objects.filter(slug="batch-project-one").count(), 1)
        self.assertEqual(ProjectNode.objects.filter(slug="batch-project-two").count(), 1)

    def test_batch_compile_endpoint_atomic_rolls_back_on_failure(self):
        url = reverse("project_middle_layer:project-middle-layer-compile-batch")
        response = self.client.post(
            url,
            {
                "projects": [
                    {
                        "title": "Atomic Project Good",
                        "intent": "community_program",
                        "tier": "public",
                        "tags": ["storytelling", "community"],
                    },
                    {
                        "title": "Atomic Project Bad",
                        "tier": "public",
                        "tags": ["oops"],
                    },
                ],
                "atomic": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "rolled_back")
        self.assertEqual(ProjectNode.objects.filter(slug="atomic-project-good").count(), 0)

    def test_export_endpoint_returns_semantic_payload(self):
        ProjectNode.objects.create(
            slug="api-export-project",
            name="API Export Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["community", "export"]},
        )

        url = reverse("project_middle_layer:project-middle-layer-export")
        response = self.client.get(url, {"scope": "all", "include_history": False})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("summary", response.data)
        self.assertGreaterEqual(response.data["summary"]["project_count"], 1)
        self.assertIn("projects", response.data)

    def test_export_endpoint_download_sets_attachment_header(self):
        ProjectNode.objects.create(
            slug="api-export-download-project",
            name="API Export Download Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["community", "download"]},
        )

        url = reverse("project_middle_layer:project-middle-layer-export")
        response = self.client.get(url, {"scope": "all", "download": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("attachment;", response["Content-Disposition"])

    def test_pipeline_run_endpoint_executes_pipeline(self):
        SemanticPipeline.objects.create(
            name="API Pipeline",
            slug="api-pipeline",
            steps=[
                {
                    "action": "compile",
                    "payload": {
                        "title": "Pipeline API Project",
                        "intent": "community_program",
                        "tier": "public",
                        "tags": ["pipeline", "api"],
                    },
                }
            ],
            triggers={"mode": "manual"},
        )

        url = reverse("project_middle_layer:project-middle-layer-pipeline-run")
        response = self.client.post(url, {"pipeline_slug": "api-pipeline"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")
        self.assertEqual(ProjectNode.objects.filter(slug="pipeline-api-project").count(), 1)
        self.assertEqual(SemanticPipelineRun.objects.filter(pipeline__slug="api-pipeline").count(), 1)

    def test_schedule_run_endpoint_executes_schedule(self):
        pipeline = SemanticPipeline.objects.create(
            name="Scheduled API Pipeline",
            slug="scheduled-api-pipeline",
            steps=[
                {
                    "action": "compile",
                    "payload": {
                        "title": "Scheduled API Project",
                        "intent": "community_program",
                        "tier": "public",
                        "tags": ["schedule", "api"],
                    },
                }
            ],
            triggers={"mode": "manual"},
        )
        SemanticSchedule.objects.create(
            name="API Schedule",
            slug="api-schedule",
            cron_expression="*/30 * * * *",
            action="pipeline-run",
            pipeline=pipeline,
            payload={},
            is_paused=False,
        )

        url = reverse("project_middle_layer:project-middle-layer-schedule-run")
        response = self.client.post(url, {"schedule_slug": "api-schedule"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")
        self.assertEqual(ProjectNode.objects.filter(slug="scheduled-api-project").count(), 1)
        self.assertEqual(SemanticScheduleRun.objects.filter(schedule__slug="api-schedule").count(), 1)

    def test_integration_inbound_sync_endpoint_compiles_project(self):
        SemanticIntegration.objects.create(
            name="Inbound API Integration",
            slug="inbound-api-integration",
            direction="inbound",
            target_system="external-cms",
            api_key="inbound-api-key",
            permissions=["inbound.sync"],
            status="active",
        )

        url = reverse("project_middle_layer:project-middle-layer-integration-inbound-sync")
        response = self.client.post(
            url,
            {
                "payload": {
                    "title": "Inbound API Project",
                    "intent": "community_program",
                    "tier": "public",
                    "tags": ["integration", "inbound"],
                }
            },
            format="json",
            HTTP_X_SEMANTIC_INTEGRATION_KEY="inbound-api-key",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["project"]["slug"], "inbound-api-project")
        self.assertEqual(ProjectNode.objects.filter(slug="inbound-api-project").count(), 1)

    def test_integration_outbound_sync_endpoint_returns_export(self):
        ProjectNode.objects.create(
            slug="integration-export-project",
            name="Integration Export Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["integration", "export"]},
        )
        SemanticIntegration.objects.create(
            name="Outbound API Integration",
            slug="outbound-api-integration",
            direction="outbound",
            target_system="analytics",
            api_key="outbound-api-key",
            permissions=["outbound.export"],
            status="active",
        )

        url = reverse("project_middle_layer:project-middle-layer-integration-outbound-sync")
        response = self.client.post(
            url,
            {
                "scope": "project",
                "project_slug": "integration-export-project",
                "include_history": False,
                "max_items": 10,
            },
            format="json",
            HTTP_X_SEMANTIC_INTEGRATION_KEY="outbound-api-key",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"]["project_count"], 1)

    def test_search_endpoint_returns_results(self):
        ProjectNode.objects.create(
            slug="searchable-project",
            name="Searchable Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["search", "semantic"]},
        )

        url = reverse("project_middle_layer:project-middle-layer-search")
        response = self.client.get(url, {"q": "search"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("summary", response.data)
        self.assertGreaterEqual(response.data["summary"]["total"], 1)

    def test_analytics_endpoint_returns_compact_trend_payload(self):
        project = ProjectNode.objects.create(
            slug="analytics-api-project",
            name="Analytics API Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["analytics", "api"], "visibility_tier": "public"},
        )
        ProjectEvolutionSnapshot.objects.create(
            project=project,
            identity_payload={"identity": {"identity_uri": "cpndc://project/analytics-api-project"}},
            drift_forecast={"risk": {"blended_semantic_drift_risk": 0.32}},
            branch_resolution={"selected_branch": "stabilization_branch"},
            specialized_path={"forms": [{"final_identity_uri": "cpndc://final/analytics-api-project/stabilization_branch"}]},
            semantic_tags=["analytics", "api"],
            identity_uri="cpndc://project/analytics-api-project",
            branch_name="stabilization_branch",
            drift_risk=0.32,
            confidence_score=74,
            confidence_label="Moderate",
            schema_issue_count=0,
            recommendations=[{"label": "Maintain"}],
        )

        # Seed an analytics snapshot so clients have immediate trend material.
        self.client.post(reverse("project_middle_layer:analytics"), {"branch_filter": "stabilization_branch", "tier_filter": "public"}, follow=True)

        url = reverse("project_middle_layer:project-middle-layer-analytics")
        response = self.client.get(url, {"branch_filter": "stabilization_branch", "tier_filter": "public", "limit": 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("summary", response.data)
        self.assertIn("filters", response.data)
        self.assertIn("trend_points", response.data)
        self.assertIn("facets", response.data)
        self.assertEqual(response.data["filters"].get("branch"), "stabilization_branch")
        self.assertEqual(response.data["filters"].get("tier"), "public")

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_version_commit_endpoint_succeeds_with_capability(self):
        self._grant_capabilities(self.user, ["version.commit"])
        ProjectNode.objects.create(
            slug="version-commit-project",
            name="Version Commit Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["version", "commit"]},
        )

        url = reverse("project_middle_layer:project-middle-layer-version-commit")
        response = self.client.post(
            url,
            {"project_slug": "version-commit-project", "message": "Initial version"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["version_number"], 1)

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_version_commit_endpoint_returns_not_found_for_missing_project(self):
        self._grant_capabilities(self.user, ["version.commit"])

        url = reverse("project_middle_layer:project-middle-layer-version-commit")
        response = self.client.post(
            url,
            {"project_slug": "missing-project", "message": "Initial version"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_version_commit_endpoint_denies_without_profile_in_strict_mode(self):
        ProjectNode.objects.create(
            slug="version-denied-project",
            name="Version Denied Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["version", "denied"]},
        )

        url = reverse("project_middle_layer:project-middle-layer-version-commit")
        response = self.client.post(
            url,
            {"project_slug": "version-denied-project", "message": "Should deny"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_version_checkout_endpoint_succeeds_with_capability(self):
        self._grant_capabilities(self.user, ["version.checkout"])
        project = ProjectNode.objects.create(
            slug="version-checkout-project",
            name="Version Checkout Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["version", "checkout"]},
        )
        version = SemanticVersion.objects.create(
            project=project,
            version_number=1,
            author=self.user,
            message="v1",
        )

        url = reverse("project_middle_layer:project-middle-layer-version-checkout")
        response = self.client.post(url, {"version_id": version.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["restored"])

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_version_checkout_endpoint_returns_not_found_for_missing_version(self):
        self._grant_capabilities(self.user, ["version.checkout"])

        url = reverse("project_middle_layer:project-middle-layer-version-checkout")
        response = self.client.post(url, {"version_id": 999999}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_version_checkout_endpoint_denies_without_profile_in_strict_mode(self):
        url = reverse("project_middle_layer:project-middle-layer-version-checkout")
        response = self.client.post(url, {"version_id": 1}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_merge_endpoint_returns_conflicts_payload(self):
        self._grant_capabilities(self.user, ["merge.semantic"])

        url = reverse("project_middle_layer:project-middle-layer-merge")
        response = self.client.post(
            url,
            {
                "base": {"title": "Seed"},
                "left": {"title": "Branch Left"},
                "right": {"title": "Branch Right"},
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_conflicts"])
        self.assertEqual(response.data["conflicts"][0]["field"], "title")

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_merge_endpoint_denies_without_profile_in_strict_mode(self):
        url = reverse("project_middle_layer:project-middle-layer-merge")
        response = self.client.post(
            url,
            {
                "base": {"title": "Seed"},
                "left": {"title": "Left"},
                "right": {"title": "Right"},
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_collaboration_heartbeat_and_release_endpoints_succeed_for_owner(self):
        self._grant_capabilities(self.user, ["edit.semantic"])
        project = ProjectNode.objects.create(
            slug="collab-project",
            name="Collaboration Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["collaboration"]},
        )

        acquire_url = reverse("project_middle_layer:project-middle-layer-collaboration-session-acquire")
        acquire_response = self.client.post(
            acquire_url,
            {"project_slug": project.slug, "lease_minutes": 20},
            format="json",
        )
        self.assertEqual(acquire_response.status_code, status.HTTP_200_OK)
        session_id = acquire_response.data["session_id"]

        heartbeat_url = reverse("project_middle_layer:project-middle-layer-collaboration-session-heartbeat")
        heartbeat_response = self.client.post(
            heartbeat_url,
            {"session_id": session_id, "lease_minutes": 30},
            format="json",
        )
        self.assertEqual(heartbeat_response.status_code, status.HTTP_200_OK)
        self.assertEqual(heartbeat_response.data["status"], "active")

        release_url = reverse("project_middle_layer:project-middle-layer-collaboration-session-release")
        release_response = self.client.post(
            release_url,
            {"session_id": session_id},
            format="json",
        )
        self.assertEqual(release_response.status_code, status.HTTP_200_OK)
        self.assertEqual(release_response.data["status"], "released")

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_collaboration_heartbeat_endpoint_returns_not_found_for_missing_session(self):
        self._grant_capabilities(self.user, ["edit.semantic"])
        url = reverse("project_middle_layer:project-middle-layer-collaboration-session-heartbeat")
        response = self.client.post(url, {"session_id": 999999}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_collaboration_release_endpoint_returns_not_found_for_missing_session(self):
        self._grant_capabilities(self.user, ["edit.semantic"])
        url = reverse("project_middle_layer:project-middle-layer-collaboration-session-release")
        response = self.client.post(url, {"session_id": 999999}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_collaboration_heartbeat_and_release_endpoints_deny_without_profile(self):
        heartbeat_url = reverse("project_middle_layer:project-middle-layer-collaboration-session-heartbeat")
        release_url = reverse("project_middle_layer:project-middle-layer-collaboration-session-release")
        heartbeat_response = self.client.post(heartbeat_url, {"session_id": 1}, format="json")
        release_response = self.client.post(release_url, {"session_id": 1}, format="json")
        self.assertEqual(heartbeat_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(release_response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_collaboration_heartbeat_and_release_require_session_owner(self):
        self._grant_capabilities(self.user, ["edit.semantic"])
        project = ProjectNode.objects.create(
            slug="collab-owner-project",
            name="Collaboration Owner Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["collaboration", "owner"]},
        )
        session = SemanticEditSession.objects.create(
            user=self.user,
            project=project,
            status="active",
        )

        other_user = User.objects.create_user(
            email="other@example.com",
            username="other",
            name="Other User",
            password="testpass123",
        )
        self._grant_capabilities(other_user, ["edit.semantic"])
        self.client.force_authenticate(user=other_user)

        heartbeat_url = reverse("project_middle_layer:project-middle-layer-collaboration-session-heartbeat")
        release_url = reverse("project_middle_layer:project-middle-layer-collaboration-session-release")
        heartbeat_response = self.client.post(heartbeat_url, {"session_id": session.id}, format="json")
        release_response = self.client.post(release_url, {"session_id": session.id}, format="json")
        self.assertEqual(heartbeat_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(release_response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_marketplace_install_endpoint_installs_latest_version(self):
        self._grant_capabilities(self.user, ["manage.marketplace"])
        item = MarketplaceItem.objects.create(
            slug="semantic-market-item",
            name="Semantic Market Item",
            item_type="plugin",
            current_version="1.2.0",
            metadata={},
            is_active=True,
        )
        MarketplaceVersion.objects.create(item=item, version="1.0.0", changelog="base")
        MarketplaceVersion.objects.create(item=item, version="1.2.0", changelog="latest")

        url = reverse("project_middle_layer:project-middle-layer-marketplace-install")
        response = self.client.post(url, {"item_slug": item.slug}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["installed_version"], "1.2.0")

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_extension_apply_endpoint_updates_state(self):
        self._grant_capabilities(self.user, ["manage.extensions"])
        extension = SemanticExtension.objects.create(
            name="Schema Patch",
            slug="schema-patch",
            schema_patch={"field": "value"},
            rules_patch={"rule": "allow"},
            version="0.0.1",
        )

        url = reverse("project_middle_layer:project-middle-layer-extension-apply")
        response = self.client.post(url, {"extension_slug": extension.slug}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        extension.refresh_from_db()
        self.assertTrue(extension.is_applied)

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_gateway_dispatch_endpoint_returns_route_availability(self):
        self._grant_capabilities(self.user, ["gateway.dispatch"])
        url = reverse("project_middle_layer:project-middle-layer-gateway-dispatch")
        response = self.client.post(url, {"route": "export", "requested_version": "v1"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["available"])

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_btif_plus_export_endpoint_returns_validation(self):
        self._grant_capabilities(self.user, ["btif.interop"])
        ProjectNode.objects.create(
            slug="btif-export-project",
            name="BTIF Export Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["btif", "export"]},
        )

        url = reverse("project_middle_layer:project-middle-layer-btif-plus-export")
        response = self.client.post(url, {"project_slug": "btif-export-project"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("payload", response.data)
        self.assertTrue(response.data["validation"]["valid"])

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_external_agent_register_and_run_endpoints(self):
        self._grant_capabilities(self.user, ["manage.external_agents"])
        register_url = reverse("project_middle_layer:project-middle-layer-external-agent-register")
        register_response = self.client.post(
            register_url,
            {
                "name": "External Runner",
                "slug": "external-runner",
                "endpoint": "https://example.com/agent",
                "capabilities": ["analyze"],
                "status": "active",
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, status.HTTP_200_OK)

        run_url = reverse("project_middle_layer:project-middle-layer-external-agent-run")
        run_response = self.client.post(
            run_url,
            {
                "agent_slug": "external-runner",
                "operation": "analyze",
                "payload": {"scope": "local"},
            },
            format="json",
        )
        self.assertEqual(run_response.status_code, status.HTTP_200_OK)
        self.assertEqual(run_response.data["status"], "completed")

    @override_settings(PROJECT_MIDDLE_LAYER_STRICT_PERMISSIONS=True)
    def test_cross_sync_run_endpoint_creates_log(self):
        self._grant_capabilities(self.user, ["sync.cross_platform"])
        ProjectNode.objects.create(
            slug="cross-sync-project",
            name="Cross Sync Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["cross", "sync"]},
        )

        url = reverse("project_middle_layer:project-middle-layer-cross-sync-run")
        response = self.client.post(
            url,
            {
                "sync_type": "delta",
                "target_platform": "partner-cloud",
                "project_slug": "cross-sync-project",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")
        self.assertEqual(SemanticCrossSyncLog.objects.count(), 1)


class ProjectMiddleLayerAdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            name="Admin User",
            password="testpass123",
        )
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.client.force_login(self.user)

        ProjectNode.objects.create(
            slug="admin-project",
            name="Admin Project",
            semantic_intent="ExpandAndIntegrate",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["project", "admin", "identity"], "visibility_tier": "public"},
        )

    def test_platform_dashboard_shows_project_middle_layer_button(self):
        response = self.client.get(reverse("admin:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Project Middle Layer Admin")

    def test_project_middle_layer_admin_page_renders_scoped_content(self):
        response = self.client.get(reverse("admin:project-middle-layer-admin"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Project Middle Layer Admin")
        self.assertContains(response, "Semantic Health Dashboard")
        self.assertContains(response, "Health Score")
        self.assertContains(response, "Admin Project")
        self.assertContains(response, "Selected Branch")
        self.assertContains(response, "Compile Project")
        self.assertContains(response, "Evolution Timeline")
        self.assertContains(response, "Identity Confidence")
        self.assertContains(response, "Lineage Explorer")
        self.assertContains(response, "Drift Heatmap")
        self.assertContains(response, "Stability Analyzer")
        self.assertContains(response, "Semantic Alerts")
        self.assertContains(response, "Semantic Recommendations")
        self.assertContains(response, "Batch Compile")
        self.assertContains(response, "Semantic Export")
        self.assertContains(response, "Semantic Pipelines")
        self.assertContains(response, "Semantic Schedules")
        self.assertContains(response, "Semantic Webhooks")
        self.assertContains(response, "Semantic Integrations")
        self.assertContains(response, "Semantic Analytics")
        self.assertContains(response, "System Dashboard")
        self.assertContains(response, "Semantic Search")
        self.assertContains(response, "Semantic Insights")
        self.assertContains(response, "Semantic Agents")
        self.assertContains(response, "Semantic Roles")
        self.assertContains(response, "Collaboration")
        self.assertContains(response, "Change Requests")
        self.assertContains(response, "Audit Logs")
        self.assertContains(response, "Semantic Versions")
        self.assertContains(response, "Merge Resolution")
        self.assertContains(response, "Replication")
        self.assertContains(response, "Federation")
        self.assertContains(response, "Shards")
        self.assertContains(response, "Cache")
        self.assertContains(response, "Sync")
        self.assertContains(response, "Distributed Agents")
        self.assertContains(response, "Density: Comfortable")
        self.assertContains(response, "Seed Demo Data")
        self.assertContains(response, "pm-health-trends-data")

    def test_project_middle_layer_seed_demo_data_action_runs_command(self):
        response = self.client.post(
            reverse("project_middle_layer:seed-demo-data"),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seed demo data completed")
        self.assertTrue(MarketplaceItem.objects.filter(slug="semantic-starter-plugin-pack").exists())

    def test_project_middle_layer_roles_page_creates_role_and_permission(self):
        role_response = self.client.post(
            reverse("project_middle_layer:roles"),
            {
                "action": "create-role",
                "name": "Semantic Reviewer",
                "slug": "semantic-reviewer",
                "capabilities_csv": "view.semantic, review.request, review.approve",
            },
            follow=True,
        )

        self.assertEqual(role_response.status_code, 200)
        role = SemanticRole.objects.get(slug="semantic-reviewer")
        self.assertIn("review.approve", role.capabilities)

        user = User.objects.create_user(
            email="reviewer@example.com",
            username="reviewer",
            name="Reviewer User",
            password="testpass123",
        )
        permission_response = self.client.post(
            reverse("project_middle_layer:roles"),
            {
                "action": "assign-permission",
                "username": "reviewer",
                "role_slug": "semantic-reviewer",
                "project_slug": "admin-project",
                "tier": "public",
                "branch": "stabilization_branch",
            },
            follow=True,
        )

        self.assertEqual(permission_response.status_code, 200)
        self.assertEqual(SemanticPermission.objects.filter(user=user, role=role).count(), 1)

    def test_project_middle_layer_collaboration_page_acquires_session(self):
        response = self.client.post(
            reverse("project_middle_layer:collaboration"),
            {
                "project_slug": "admin-project",
                "force_takeover": False,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SemanticEditSession.objects.filter(project__slug="admin-project", user=self.user).count(), 1)

    def test_project_middle_layer_change_requests_create_and_review(self):
        create_response = self.client.post(
            reverse("project_middle_layer:change-requests"),
            {
                "action": "create-change-request",
                "project_slug": "admin-project",
                "proposed_changes_json": '{"name": "Admin Project Updated"}',
            },
            follow=True,
        )

        self.assertEqual(create_response.status_code, 200)
        change = SemanticChangeRequest.objects.latest("id")
        self.assertEqual(change.status, "pending")

        review_response = self.client.post(
            reverse("project_middle_layer:change-requests"),
            {
                "action": "review-change-request",
                "change_request_id": change.id,
                "approve": True,
                "notes": "Looks good",
            },
            follow=True,
        )

        self.assertEqual(review_response.status_code, 200)
        change.refresh_from_db()
        self.assertEqual(change.status, "approved")
        self.assertEqual(ProjectNode.objects.get(slug="admin-project").name, "Admin Project Updated")

    def test_project_middle_layer_versions_commit_and_checkout(self):
        project = ProjectNode.objects.get(slug="admin-project")
        ProjectEvolutionSnapshot.objects.create(
            project=project,
            identity_payload={"identity": {"identity_uri": "cpndc://project/admin-project-v1", "slug": "admin-project"}},
            drift_forecast={"risk": {"blended_semantic_drift_risk": 0.2}},
            branch_resolution={"selected_branch": "stabilization_branch"},
            specialized_path={"forms": [{"final_identity_uri": "cpndc://final/admin-project/stabilization_branch"}]},
            semantic_tags=["project", "admin"],
            identity_uri="cpndc://project/admin-project-v1",
            branch_name="stabilization_branch",
            drift_risk=0.2,
        )

        commit_response = self.client.post(
            reverse("project_middle_layer:versions"),
            {
                "action": "commit-version",
                "project_slug": "admin-project",
                "message": "checkpoint",
            },
            follow=True,
        )

        self.assertEqual(commit_response.status_code, 200)
        version = SemanticVersion.objects.latest("id")
        self.assertEqual(version.version_number, 1)

        checkout_response = self.client.post(
            reverse("project_middle_layer:versions"),
            {
                "action": "checkout-version",
                "version_id": version.id,
            },
            follow=True,
        )
        self.assertEqual(checkout_response.status_code, 200)

    def test_project_middle_layer_merge_page_computes_conflicts(self):
        response = self.client.post(
            reverse("project_middle_layer:merge"),
            {
                "left_json": '{"name": "left", "tier": "public"}',
                "right_json": '{"name": "right", "tier": "public"}',
                "base_json": '{"name": "base", "tier": "public"}',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Merged Output")
        self.assertContains(response, "Conflicts")

    def test_phase8_actions_record_audit_logs(self):
        self.client.get(reverse("project_middle_layer:insights"))
        self.assertGreaterEqual(SemanticAuditLog.objects.filter(action="insights.semantic").count(), 1)

    def test_project_middle_layer_analytics_page_generates_snapshot(self):
        post_response = self.client.post(
            reverse("project_middle_layer:analytics"),
            follow=True,
        )

        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, "Generated semantic analytics snapshot")
        self.assertGreaterEqual(SemanticAnalyticsSnapshot.objects.count(), 1)

    def test_analytics_snapshot_persists_filters_and_chart_series(self):
        project = ProjectNode.objects.get(slug="admin-project")
        ProjectEvolutionSnapshot.objects.create(
            project=project,
            identity_payload={"identity": {"identity_uri": "cpndc://project/admin-project"}},
            drift_forecast={"risk": {"blended_semantic_drift_risk": 0.7}},
            branch_resolution={"selected_branch": "stabilization_branch"},
            specialized_path={"forms": [{"final_identity_uri": "cpndc://final/admin-project/stabilization_branch"}]},
            semantic_tags=["project", "admin"],
            identity_uri="cpndc://project/admin-project",
            branch_name="stabilization_branch",
            drift_risk=0.7,
            confidence_score=62,
            confidence_label="Moderate",
            schema_issue_count=0,
            recommendations=[{"label": "Tune tags"}],
        )

        post_response = self.client.post(
            reverse("project_middle_layer:analytics"),
            {
                "branch_filter": "stabilization_branch",
                "tier_filter": "public",
                "limit": 20,
            },
            follow=True,
        )

        self.assertEqual(post_response.status_code, 200)
        latest = SemanticAnalyticsSnapshot.objects.first()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.branch_filter, "stabilization_branch")
        self.assertEqual(latest.tier_filter, "public")
        self.assertGreaterEqual(len(latest.chart_series), 1)

    def test_project_middle_layer_dashboard_page_renders(self):
        SemanticAnalyticsSnapshot.objects.create(
            metrics={"seeded": True},
            project_count=1,
            drift_mean=0.12,
            drift_std=0.01,
            confidence_mean=81.0,
            confidence_std=2.0,
            stability_mean=77.0,
            stability_std=3.0,
            lineage_cluster_map={"community": 1},
            tag_frequency_map={"admin": 1},
        )

        response = self.client.get(reverse("project_middle_layer:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Semantic System Dashboard")

    def test_project_middle_layer_search_page_renders_results(self):
        response = self.client.get(reverse("project_middle_layer:search"), {"q": "admin"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Semantic Search")
        self.assertContains(response, "Summary")

    def test_project_middle_layer_insights_page_renders(self):
        response = self.client.get(reverse("project_middle_layer:insights"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Semantic Insights")

    def test_insights_include_adoption_and_compile_patterns(self):
        project = ProjectNode.objects.get(slug="admin-project")

        ProjectEvolutionSnapshot.objects.create(
            project=project,
            identity_payload={"identity": {"identity_uri": "cpndc://project/admin-project"}},
            drift_forecast={"risk": {"blended_semantic_drift_risk": 0.3}},
            branch_resolution={"selected_branch": "stabilization_branch"},
            specialized_path={"forms": [{"final_identity_uri": "cpndc://final/admin-project/stabilization_branch"}]},
            semantic_tags=["project", "admin"],
            identity_uri="cpndc://project/admin-project",
            branch_name="stabilization_branch",
            drift_risk=0.3,
            confidence_score=55,
            confidence_label="Volatile",
            schema_issue_count=0,
            recommendations=[{"label": "Reduce drift"}],
        )
        ProjectEvolutionSnapshot.objects.create(
            project=project,
            identity_payload={"identity": {"identity_uri": "cpndc://project/admin-project-v2"}},
            drift_forecast={"risk": {"blended_semantic_drift_risk": 0.2}},
            branch_resolution={"selected_branch": "stabilization_branch"},
            specialized_path={"forms": [{"final_identity_uri": "cpndc://final/admin-project/stabilization_branch"}]},
            semantic_tags=["project", "admin"],
            identity_uri="cpndc://project/admin-project-v2",
            branch_name="stabilization_branch",
            drift_risk=0.2,
            confidence_score=70,
            confidence_label="Moderate",
            schema_issue_count=0,
            recommendations=[],
        )

        pipeline = SemanticPipeline.objects.create(
            name="Insight Pattern Pipeline",
            slug="insight-pattern-pipeline",
            steps=[],
            triggers={"mode": "manual"},
            is_active=True,
        )
        SemanticPipelineRun.objects.create(pipeline=pipeline, status="completed", triggered_by="test", result={})
        SemanticPipelineRun.objects.create(pipeline=pipeline, status="failed", triggered_by="test", result={}, error_message="failed")

        response = self.client.get(reverse("project_middle_layer:insights"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recommendation adoption effectiveness")
        self.assertContains(response, "Compile orchestration success/failure pattern")

    def test_project_middle_layer_agents_page_runs_agent(self):
        response = self.client.post(
            reverse("project_middle_layer:agents"),
            {"agent_name": "Drift Agent"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Drift Agent completed")
        self.assertGreaterEqual(SemanticAgentRun.objects.count(), 1)

    def test_drift_agent_triggers_pipeline_when_drift_high(self):
        project = ProjectNode.objects.get(slug="admin-project")
        ProjectEvolutionSnapshot.objects.create(
            project=project,
            identity_payload={"identity": {"identity_uri": "cpndc://project/admin-project"}},
            drift_forecast={"risk": {"blended_semantic_drift_risk": 0.85}},
            branch_resolution={"selected_branch": "stabilization_branch"},
            specialized_path={"forms": [{"final_identity_uri": "cpndc://final/admin-project/stabilization_branch"}]},
            semantic_tags=["project", "admin"],
            identity_uri="cpndc://project/admin-project",
            branch_name="stabilization_branch",
            drift_risk=0.85,
            confidence_score=52,
            confidence_label="Volatile",
            schema_issue_count=0,
            recommendations=[{"label": "Reduce drift"}],
        )

        SemanticPipeline.objects.create(
            name="Drift Agent Pipeline",
            slug="drift-agent-pipeline",
            steps=[
                {
                    "action": "compile",
                    "payload": {
                        "title": "Drift Agent Triggered Project",
                        "intent": "community_program",
                        "tier": "public",
                        "tags": ["agent", "drift"],
                    },
                }
            ],
            triggers={"mode": "manual"},
            is_active=True,
        )

        response = self.client.post(
            reverse("project_middle_layer:agents"),
            {"agent_name": "Drift Agent"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(SemanticPipelineRun.objects.filter(pipeline__slug="drift-agent-pipeline").count(), 1)
        run = SemanticAgentRun.objects.first()
        self.assertIsNotNone(run)
        self.assertTrue(any(item.get("action") == "pipeline_trigger" for item in (run.actions_taken or [])))

    def test_project_middle_layer_compile_page_creates_node_and_redirects(self):
        response = self.client.post(
            reverse("project_middle_layer:compile"),
            {
                "title": "Admin Shortcut Project",
                "intent": "community_program",
                "tier": "public",
                "description": "Created through the admin shortcut.",
                "tags": "storytelling, community, workshops, local-media",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Project Middle Layer Admin")
        node = ProjectNode.objects.get(slug="admin-shortcut-project")
        self.assertEqual(node.name, "Admin Shortcut Project")
        self.assertEqual(node.metadata.get("visibility_tier"), "public")
        self.assertEqual(ProjectEvolutionSnapshot.objects.filter(project=node).count(), 1)
        self.assertEqual(SemanticLineageRecord.objects.filter(project=node).count(), 1)
        snapshot = ProjectEvolutionSnapshot.objects.filter(project=node).latest("created_at")
        self.assertGreaterEqual(snapshot.confidence_score, 0)
        self.assertIn(snapshot.confidence_label, {"Stable", "Moderate", "Volatile"})
        self.assertEqual(snapshot.schema_issue_count, 0)
        self.assertGreaterEqual(len(snapshot.recommendations), 1)
        lineage_record = SemanticLineageRecord.objects.filter(project=node).latest("created_at")
        self.assertIn("semantic_clusters", lineage_record.lineage_tree or {})
        self.assertGreaterEqual(len(lineage_record.recommendations), 1)
        self.assertGreaterEqual(SemanticAlert.objects.filter(project=node).count(), 1)

    def test_project_middle_layer_alerts_page_renders(self):
        ProjectNode.objects.create(
            slug="alert-project",
            name="Alert Project",
            semantic_intent="community_program",
            mlas_tier="Semantic Utility",
            btif_classification="ExpansionFlow",
            metadata={"semantic_tags": ["story"]},
        )
        project = ProjectNode.objects.get(slug="alert-project")
        SemanticAlert.objects.create(
            project=project,
            alert_type="high_drift",
            severity="high",
            message="Alert Project has high semantic drift risk.",
        )

        response = self.client.get(reverse("project_middle_layer:alerts"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Semantic Alerts")
        self.assertContains(response, "Alert Project")
        self.assertContains(response, "high_drift")

    def test_project_middle_layer_recommendations_page_renders(self):
        response = self.client.get(reverse("project_middle_layer:recommendations"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Semantic Recommendations")
        self.assertContains(response, "Admin Project")
        self.assertContains(response, "Apply Recommendation")

    def test_project_middle_layer_timeline_page_renders_snapshots(self):
        ProjectEvolutionSnapshot.objects.create(
            project=ProjectNode.objects.get(slug="admin-project"),
            identity_payload={"identity": {"identity_uri": "cpndc://project/admin-project"}},
            drift_forecast={"risk": {"blended_semantic_drift_risk": 0.2}},
            branch_resolution={"selected_branch": "stabilization_branch"},
            specialized_path={"forms": [{"final_identity_uri": "cpndc://final/admin-project/stabilization_branch"}]},
            semantic_tags=["project", "admin", "identity"],
            identity_uri="cpndc://project/admin-project",
            branch_name="stabilization_branch",
            drift_risk=0.2,
        )

        response = self.client.get(reverse("project_middle_layer:timeline"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Semantic Evolution Timeline")
        self.assertContains(response, "Admin Project")
        self.assertContains(response, "stabilization_branch")
        self.assertContains(response, "Confidence")

    def test_project_middle_layer_diff_viewer_renders(self):
        project = ProjectNode.objects.get(slug="admin-project")
        older = ProjectEvolutionSnapshot.objects.create(
            project=project,
            identity_payload={"identity": {"identity_uri": "cpndc://project/admin-project"}},
            drift_forecast={"risk": {"blended_semantic_drift_risk": 0.2}},
            branch_resolution={"selected_branch": "stabilization_branch"},
            specialized_path={"forms": [{"final_identity_uri": "cpndc://final/admin-project/stabilization_branch"}]},
            semantic_tags=["project", "admin"],
            identity_uri="cpndc://project/admin-project",
            branch_name="stabilization_branch",
            drift_risk=0.2,
            confidence_score=82,
            confidence_label="Stable",
            schema_issue_count=0,
            recommendations=[],
        )
        newer = ProjectEvolutionSnapshot.objects.create(
            project=project,
            identity_payload={"identity": {"identity_uri": "cpndc://project/admin-project-v2"}},
            drift_forecast={"risk": {"blended_semantic_drift_risk": 0.5}},
            branch_resolution={"selected_branch": "expansion_integration_branch"},
            specialized_path={"forms": [{"final_identity_uri": "cpndc://final/admin-project/expansion_integration_branch"}]},
            semantic_tags=["project", "admin", "identity"],
            identity_uri="cpndc://project/admin-project-v2",
            branch_name="expansion_integration_branch",
            drift_risk=0.5,
            confidence_score=67,
            confidence_label="Moderate",
            schema_issue_count=0,
            recommendations=[],
        )

        response = self.client.get(
            reverse("project_middle_layer:diff"),
            {
                "snapshot_a": older.id,
                "snapshot_b": newer.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Semantic Diff Viewer")
        self.assertContains(response, "Tag Changes")
        self.assertContains(response, "Metric Deltas")
        self.assertContains(response, "Branch and Identity")

    def test_project_middle_layer_lineage_explorer_page_renders(self):
        response = self.client.get(reverse("project_middle_layer:lineage"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Semantic Lineage Explorer")
        self.assertContains(response, "Lineage Records")
        self.assertContains(response, "Admin Project")

    def test_project_middle_layer_batch_compile_page_renders_and_compiles(self):
        response = self.client.post(
            reverse("project_middle_layer:batch-compile"),
            {
                "payload_json": """[
    {
        \"title\": \"Batch Admin One\",
        \"intent\": \"community_program\",
        \"tier\": \"public\",
        \"tags\": [\"storytelling\", \"community\"]
    },
    {
        \"title\": \"Batch Admin Two\",
        \"intent\": \"education_flow\",
        \"tier\": \"public\",
        \"tags\": [\"learning\", \"community\"]
    }
]""",
                "atomic": False,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Batch Summary")
        self.assertContains(response, "Compiled 2 of 2 payloads")
        self.assertEqual(ProjectNode.objects.filter(slug="batch-admin-one").count(), 1)
        self.assertEqual(ProjectNode.objects.filter(slug="batch-admin-two").count(), 1)

    def test_project_middle_layer_export_page_renders_summary_preview(self):
        response = self.client.post(
            reverse("project_middle_layer:export"),
            {
                "scope": "project",
                "project_slug": "admin-project",
                "include_history": False,
                "download": False,
                "max_items": 25,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Export Summary")
        self.assertContains(response, "admin-project")

    def test_project_middle_layer_export_page_downloads_json(self):
        response = self.client.post(
            reverse("project_middle_layer:export"),
            {
                "scope": "project",
                "project_slug": "admin-project",
                "include_history": False,
                "download": True,
                "max_items": 25,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("attachment;", response["Content-Disposition"])

    def test_project_middle_layer_pipelines_page_creates_and_runs_pipeline(self):
        create_response = self.client.post(
            reverse("project_middle_layer:pipelines"),
            {
                "name": "Admin Pipeline",
                "slug": "admin-pipeline",
                "steps_json": """[
    {
        \"action\": \"compile\",
        \"payload\": {
            \"title\": \"Pipeline Admin Project\",
            \"intent\": \"community_program\",
            \"tier\": \"public\",
            \"tags\": [\"pipeline\", \"admin\"]
        }
    },
    {
        \"action\": \"export\",
        \"payload\": {
            \"scope\": \"all\",
            \"include_history\": false
        }
    }
]""",
                "triggers_json": "{\"mode\": \"manual\"}",
                "is_active": True,
            },
            follow=True,
        )

        self.assertEqual(create_response.status_code, 200)
        self.assertContains(create_response, "Pipeline &#x27;Admin Pipeline&#x27; saved")
        pipeline = SemanticPipeline.objects.get(slug="admin-pipeline")
        self.assertEqual(pipeline.name, "Admin Pipeline")

        run_response = self.client.post(
            reverse("project_middle_layer:pipeline-run", kwargs={"slug": "admin-pipeline"}),
            follow=True,
        )

        self.assertEqual(run_response.status_code, 200)
        self.assertContains(run_response, "completed")
        self.assertEqual(ProjectNode.objects.filter(slug="pipeline-admin-project").count(), 1)
        self.assertEqual(SemanticPipelineRun.objects.filter(pipeline=pipeline).count(), 1)

    def test_project_middle_layer_schedules_page_creates_runs_and_pauses_schedule(self):
        pipeline = SemanticPipeline.objects.create(
            name="Admin Scheduled Pipeline",
            slug="admin-scheduled-pipeline",
            steps=[
                {
                    "action": "compile",
                    "payload": {
                        "title": "Schedule Admin Project",
                        "intent": "community_program",
                        "tier": "public",
                        "tags": ["schedule", "admin"],
                    },
                }
            ],
            triggers={"mode": "manual"},
        )

        create_response = self.client.post(
            reverse("project_middle_layer:schedules"),
            {
                "name": "Admin Schedule",
                "slug": "admin-schedule",
                "cron_expression": "*/30 * * * *",
                "action": "pipeline-run",
                "pipeline_slug": pipeline.slug,
                "payload_json": "{}",
                "is_paused": False,
            },
            follow=True,
        )

        self.assertEqual(create_response.status_code, 200)
        self.assertContains(create_response, "Schedule &#x27;Admin Schedule&#x27; saved")
        schedule = SemanticSchedule.objects.get(slug="admin-schedule")
        self.assertEqual(schedule.action, "pipeline-run")

        run_response = self.client.post(
            reverse("project_middle_layer:schedule-run", kwargs={"slug": "admin-schedule"}),
            follow=True,
        )
        self.assertEqual(run_response.status_code, 200)
        self.assertContains(run_response, "completed")
        self.assertEqual(ProjectNode.objects.filter(slug="schedule-admin-project").count(), 1)
        self.assertEqual(SemanticScheduleRun.objects.filter(schedule=schedule).count(), 1)

        pause_response = self.client.post(
            reverse("project_middle_layer:schedule-pause", kwargs={"slug": "admin-schedule"}),
            follow=True,
        )
        self.assertEqual(pause_response.status_code, 200)
        self.assertContains(pause_response, "paused")
        schedule.refresh_from_db()
        self.assertTrue(schedule.is_paused)

    @patch("project_middle_layer.webhooks.urllib_request.urlopen")
    def test_compile_dispatches_webhook_delivery(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"ok"
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        webhook = SemanticWebhook.objects.create(
            name="Compile Webhook",
            target_url="https://example.com/semantic-webhook",
            event_type="compile.completed",
            status="active",
        )

        response = self.client.post(
            reverse("project_middle_layer:compile"),
            {
                "title": "Webhook Compile Project",
                "intent": "community_program",
                "tier": "public",
                "description": "Webhook dispatch test",
                "tags": "storytelling, community",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        delivery = SemanticWebhookDelivery.objects.filter(webhook=webhook).latest("created_at")
        self.assertEqual(delivery.event_type, "compile.completed")
        self.assertEqual(delivery.status, "delivered")

    def test_project_middle_layer_webhooks_page_creates_and_lists_webhook(self):
        response = self.client.post(
            reverse("project_middle_layer:webhooks"),
            {
                "name": "Admin Webhook",
                "target_url": "https://example.com/admin-webhook",
                "event_type": "pipeline.completed",
                "secret_token": "secret-123",
                "status": "active",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Webhook &#x27;Admin Webhook&#x27; saved")
        self.assertContains(response, "Admin Webhook")
        webhook = SemanticWebhook.objects.get(name="Admin Webhook")
        self.assertEqual(webhook.event_type, "pipeline.completed")

    def test_project_middle_layer_integrations_page_creates_and_lists_integration(self):
        response = self.client.post(
            reverse("project_middle_layer:integrations"),
            {
                "name": "Admin Integration",
                "slug": "admin-integration",
                "direction": "bidirectional",
                "target_system": "story-engine",
                "endpoint_url": "https://example.com/story-engine",
                "api_key": "admin-integration-key",
                "permissions_csv": "inbound.sync, outbound.export",
                "status": "active",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Integration &#x27;Admin Integration&#x27; saved")
        self.assertContains(response, "Admin Integration")
        integration = SemanticIntegration.objects.get(slug="admin-integration")
        self.assertEqual(integration.direction, "bidirectional")
        self.assertIn("inbound.sync", integration.permissions)

    def test_project_middle_layer_replication_page_saves_target_and_runs_sync(self):
        save_response = self.client.post(
            reverse("project_middle_layer:replication"),
            {
                "action": "save",
                "name": "Primary Replica",
                "slug": "primary-replica",
                "remote_node_url": "https://replica.example.com",
                "api_key": "replica-key",
                "mode": "full",
                "direction": "bidirectional",
                "is_active": True,
            },
            follow=True,
        )

        self.assertEqual(save_response.status_code, 200)
        self.assertContains(save_response, "Replication target &#x27;Primary Replica&#x27; saved")
        target = ReplicationConfig.objects.get(slug="primary-replica")
        self.assertEqual(target.last_sync_status, "idle")

        sync_response = self.client.post(
            reverse("project_middle_layer:replication"),
            {
                "action": "sync",
                "target_slug": "primary-replica",
            },
            follow=True,
        )
        self.assertEqual(sync_response.status_code, 200)
        self.assertContains(sync_response, "Replication sync for &#x27;primary-replica&#x27; completed")
        target.refresh_from_db()
        self.assertIn(target.last_sync_status, {"completed", "failed"})

    def test_project_middle_layer_federation_page_saves_peer_and_runs_search(self):
        save_response = self.client.post(
            reverse("project_middle_layer:federation"),
            {
                "name": "Peer East",
                "slug": "peer-east",
                "peer_identity": "peer:east",
                "peer_url": "https://peer-east.example.com",
                "capabilities_csv": "search,insights,sync",
                "sync_rules_json": '{"scope": "lineage"}',
                "is_active": True,
            },
            follow=True,
        )

        self.assertEqual(save_response.status_code, 200)
        self.assertContains(save_response, "Federation peer &#x27;Peer East&#x27; saved")
        peer = FederationPeer.objects.get(slug="peer-east")
        self.assertIn("search", peer.capabilities)

        search_response = self.client.get(
            reverse("project_middle_layer:federation"),
            {"q": "admin"},
        )
        self.assertEqual(search_response.status_code, 200)
        self.assertContains(search_response, "Federated Search Result")

    def test_project_middle_layer_shards_page_saves_shard_and_rebalances(self):
        save_response = self.client.post(
            reverse("project_middle_layer:shards"),
            {
                "name": "Public Tier Shard",
                "slug": "public-tier-shard",
                "node_url": "https://shard-public.example.com",
                "strategy": "tier",
                "route_value": "public",
                "is_active": True,
            },
            follow=True,
        )

        self.assertEqual(save_response.status_code, 200)
        self.assertContains(save_response, "Shard &#x27;Public Tier Shard&#x27; saved")
        shard = SemanticShard.objects.get(slug="public-tier-shard")
        self.assertEqual(shard.tier, "public")

        rebalance_response = self.client.post(
            reverse("project_middle_layer:shards"),
            {"action": "rebalance"},
            follow=True,
        )
        self.assertEqual(rebalance_response.status_code, 200)
        self.assertContains(rebalance_response, "Shard rebalance completed")

    def test_project_middle_layer_cache_page_runs_inspect_warm_and_flush(self):
        inspect_response = self.client.post(
            reverse("project_middle_layer:cache"),
            {
                "action": "inspect",
                "target": "analytics",
                "params_json": '{"limit": 5}',
            },
            follow=True,
        )
        self.assertEqual(inspect_response.status_code, 200)
        self.assertContains(inspect_response, "Cache inspect completed")

        warm_response = self.client.post(
            reverse("project_middle_layer:cache"),
            {"action": "warm"},
            follow=True,
        )
        self.assertEqual(warm_response.status_code, 200)
        self.assertContains(warm_response, "Semantic cache warmed")

        flush_response = self.client.post(
            reverse("project_middle_layer:cache"),
            {"action": "flush"},
            follow=True,
        )
        self.assertEqual(flush_response.status_code, 200)
        self.assertContains(flush_response, "Semantic cache flushed")

    def test_project_middle_layer_sync_page_creates_sync_log(self):
        ReplicationConfig.objects.create(
            name="Sync Replica",
            slug="sync-replica",
            remote_node_url="https://sync-replica.example.com",
            api_key="sync-replica-key",
            mode="full",
            direction="push",
            is_active=True,
        )

        response = self.client.post(
            reverse("project_middle_layer:sync"),
            {
                "sync_type": "version",
                "target_slug": "sync-replica",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sync run completed with status")
        self.assertGreaterEqual(SemanticSyncLog.objects.count(), 1)

    def test_project_middle_layer_distributed_agents_page_runs_agent(self):
        ReplicationConfig.objects.create(
            name="Agent Replica",
            slug="agent-replica",
            remote_node_url="https://agent-replica.example.com",
            api_key="agent-replica-key",
            mode="full",
            direction="bidirectional",
            is_active=True,
        )
        SemanticShard.objects.create(
            name="Agent Shard",
            slug="agent-shard",
            strategy="cluster",
            route_value="admin",
            cluster_label="admin",
            is_active=True,
        )

        response = self.client.post(
            reverse("project_middle_layer:distributed-agents"),
            {"agent_name": "Global Drift Agent"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Distributed agent &#x27;Global Drift Agent&#x27; completed")
        run = DistributedAgentRun.objects.first()
        self.assertIsNotNone(run)
        self.assertEqual(run.status, "completed")
        self.assertGreaterEqual(run.node_count, 1)

    def test_project_middle_layer_marketplace_page_installs_item(self):
        item = MarketplaceItem.objects.create(
            slug="admin-market-item",
            name="Admin Market Item",
            item_type="plugin",
            current_version="1.1.0",
            metadata={},
            is_active=True,
        )
        MarketplaceVersion.objects.create(item=item, version="1.0.0", changelog="Initial")
        MarketplaceVersion.objects.create(item=item, version="1.1.0", changelog="Latest")

        response = self.client.post(
            reverse("project_middle_layer:marketplace"),
            {
                "item_slug": item.slug,
                "requested_version": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "installed")

    def test_project_middle_layer_plugins_page_registers_and_toggles_plugin(self):
        create_response = self.client.post(
            reverse("project_middle_layer:plugins"),
            {
                "name": "Admin Plugin",
                "slug": "admin-plugin",
                "plugin_type": "agent",
                "entrypoint": "project_middle_layer.plugins.admin_plugin",
                "capabilities_csv": "gateway.inspect,sync.cross_platform",
                "version": "0.1.0",
                "enabled": True,
            },
            follow=True,
        )
        self.assertEqual(create_response.status_code, 200)
        self.assertContains(create_response, "Plugin &#x27;Admin Plugin&#x27; saved")

        toggle_response = self.client.post(
            reverse("project_middle_layer:plugins"),
            {
                "action": "toggle",
                "plugin_slug": "admin-plugin",
                "enabled": "0",
            },
            follow=True,
        )
        self.assertEqual(toggle_response.status_code, 200)
        plugin = SemanticPlugin.objects.get(slug="admin-plugin")
        self.assertFalse(plugin.enabled)

    def test_project_middle_layer_extensions_page_saves_applies_and_rolls_back(self):
        save_response = self.client.post(
            reverse("project_middle_layer:extensions"),
            {
                "name": "Admin Extension",
                "slug": "admin-extension",
                "version": "0.1.0",
                "schema_patch_json": '{"field": "value"}',
                "rules_patch_json": '{"rule": "allow"}',
            },
            follow=True,
        )
        self.assertEqual(save_response.status_code, 200)
        self.assertContains(save_response, "Extension &#x27;Admin Extension&#x27; saved")

        apply_response = self.client.post(
            reverse("project_middle_layer:extensions"),
            {
                "action": "apply",
                "extension_slug": "admin-extension",
            },
            follow=True,
        )
        self.assertEqual(apply_response.status_code, 200)
        extension = SemanticExtension.objects.get(slug="admin-extension")
        self.assertTrue(extension.is_applied)

        rollback_response = self.client.post(
            reverse("project_middle_layer:extensions"),
            {
                "action": "rollback",
                "extension_slug": "admin-extension",
            },
            follow=True,
        )
        self.assertEqual(rollback_response.status_code, 200)
        extension.refresh_from_db()
        self.assertFalse(extension.is_applied)

    def test_project_middle_layer_btif_plus_page_exports_and_validates(self):
        export_response = self.client.post(
            reverse("project_middle_layer:btif-plus"),
            {
                "action": "export",
                "project_slug": "admin-project",
                "payload_json": "",
            },
            follow=True,
        )
        self.assertEqual(export_response.status_code, 200)
        self.assertContains(export_response, "Validation")

        validate_response = self.client.post(
            reverse("project_middle_layer:btif-plus"),
            {
                "action": "validate",
                "project_slug": "admin-project",
                "payload_json": '{"project": {}, "identity_payload": {}, "semantic_tags": [], "lineage_graph": {}, "metrics": {}}',
            },
            follow=True,
        )
        self.assertEqual(validate_response.status_code, 200)
        self.assertContains(validate_response, "Validation")

    def test_project_middle_layer_external_agents_page_registers_and_runs_agent(self):
        register_response = self.client.post(
            reverse("project_middle_layer:external-agents"),
            {
                "name": "Admin External Agent",
                "slug": "admin-external-agent",
                "endpoint": "https://example.com/admin-agent",
                "capabilities_csv": "analyze",
                "auth_token": "",
                "status": "active",
            },
            follow=True,
        )
        self.assertEqual(register_response.status_code, 200)
        self.assertContains(register_response, "saved")

        run_response = self.client.post(
            reverse("project_middle_layer:external-agents"),
            {
                "action": "run",
                "agent_slug": "admin-external-agent",
                "operation": "analyze",
            },
            follow=True,
        )
        self.assertEqual(run_response.status_code, 200)
        self.assertContains(run_response, "completed operation")

    def test_project_middle_layer_cross_sync_page_runs_sync(self):
        response = self.client.post(
            reverse("project_middle_layer:cross-sync"),
            {
                "sync_type": "delta",
                "target_platform": "partner-cloud",
                "project_slug": "admin-project",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cross-platform sync completed")
        self.assertGreaterEqual(SemanticCrossSyncLog.objects.count(), 1)

    @patch("project_middle_layer.webhooks.urllib_request.urlopen")
    def test_webhook_retry_view_updates_delivery(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"retried"
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        webhook = SemanticWebhook.objects.create(
            name="Retry Webhook",
            target_url="https://example.com/retry-webhook",
            event_type="compile.completed",
            status="active",
        )
        delivery = SemanticWebhookDelivery.objects.create(
            webhook=webhook,
            event_type="compile.completed",
            payload={"test": True},
            status="failed",
            error_message="timeout",
        )

        response = self.client.post(
            reverse("project_middle_layer:webhook-retry", kwargs={"delivery_id": delivery.id}),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, "delivered")
        self.assertContains(response, "succeeded on retry")
