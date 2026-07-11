from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from project_middle_layer.models import ProjectNode
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


class ProjectMiddleLayerWizardAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="wizard@example.com",
            username="wizard",
            name="Wizard User",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

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
            metadata={"semantic_tags": ["project", "admin", "identity"]},
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
