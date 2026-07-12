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
