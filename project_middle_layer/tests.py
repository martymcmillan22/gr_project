from django.test import SimpleTestCase
from django.urls import reverse

from project_middle_layer.pipelines import build_project_creation_payload


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
        self.assertIn("semantic_tree", payload)
        self.assertEqual(payload["schema_validation_errors"], [])
        self.assertIn("cpndc://project-middle-layer/project-middle-layer", payload["identity_payload"]["identity"]["identity_uri"])
        self.assertIn("identity_id", payload["identity_payload"]["identity"])
        self.assertIn("IDEA", payload["tier_profile"]["lifecycle"])
        self.assertIn("SPECIALIZED_PATH", payload["tier_profile"]["lifecycle"])
        self.assertIn("Identity Branch", payload["semantic_tree"])


class ProjectMiddleLayerRouteTests(SimpleTestCase):
    def test_api_compile_route_resolves(self):
        self.assertEqual(
            reverse("project_middle_layer:project-middle-layer-compile"),
            "/project-middle-layer/api/compile/",
        )
