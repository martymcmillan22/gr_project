from django.test import SimpleTestCase

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

        self.assertIn("schema", payload)
        self.assertIn("tier_profile", payload)
        self.assertIn("identity_payload", payload)
        self.assertIn("semantic_tree", payload)
        self.assertIn("cpndc://project-middle-layer/project-middle-layer", payload["identity_payload"]["identity"]["identity_uri"])
