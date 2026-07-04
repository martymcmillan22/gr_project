from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import SemanticPreset, Slide


class MlasBtifApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(
            username="mlas_tester",
            email="mlas_tester@example.com",
            password="password12345",
        )
        cls.other_user = user_model.objects.create_user(
            username="mlas_other",
            email="mlas_other@example.com",
            password="password12345",
        )

        cls.post_preset = SemanticPreset.objects.create(
            name="post.purple.statistics",
            phase="post",
            color_primary="purple",
            metaphor="mycelium",
            mlas_subject="math",
            mlas_branch="sacp",
            mlas_term=None,
            mlas_meta=None,
            dewey_code=500,
            industry_super_sector="financials",
            industry_sector="banking",
            industry_group="financial-analytics",
            industry_sub_industry="quant-finance",
            ui_category="customer",
        )

        cls.create_preset = SemanticPreset.objects.create(
            name="create.red.math",
            phase="create",
            color_primary="red",
            metaphor="immune_system",
            mlas_subject="math",
            mlas_branch="base",
            mlas_term=None,
            mlas_meta=None,
            dewey_code=100,
            industry_super_sector="financials",
            industry_sector="banking",
            industry_group="analytics",
            industry_sub_industry="quant",
            ui_category="operations",
        )

        cls.work_delivery_preset = SemanticPreset.objects.create(
            name="work.pink.history",
            phase="work",
            color_primary="pink",
            metaphor="botanist",
            mlas_subject="history",
            mlas_branch="hist",
            mlas_term="timeline",
            mlas_meta=None,
            dewey_code=900,
            industry_super_sector="industrials",
            industry_sector="ops",
            industry_group="execution",
            industry_sub_industry="delivery",
            ui_category="delivery",
        )

    def setUp(self):
        self.client.force_login(self.user)

    def _create_slide(self, title="Slide", ui_category=None):
        return Slide.objects.create(
            title=title,
            phase="create",
            color_primary="red",
            metaphor="immune_system",
            mlas_subject="math",
            mlas_branch="base",
            mlas_term=None,
            mlas_meta=None,
            dewey_code=100,
            industry_super_sector="financials",
            industry_sector="banking",
            industry_group="analytics",
            industry_sub_industry="quant",
            ui_category=ui_category,
            phase_resolved="create",
            ui_category_resolved="operations",
            layout_archetype="matrix",
            component_pack="foundational-pack",
            nav_group="foundations",
            page_signature="analytical",
        )

    def test_slide_detail_requires_authentication(self):
        slide = self._create_slide("Slide Detail Auth")
        self.client.logout()

        response = self.client.get(f"/contracts/slides/{slide.id}/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "Authentication required."})

    def test_preset_list_requires_authentication(self):
        self.client.logout()

        response = self.client.get("/contracts/presets/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "Authentication required."})

    def test_preset_list_returns_expected_shape_and_order(self):
        response = self.client.get("/contracts/presets/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn("presets", payload)
        self.assertIsInstance(payload["presets"], list)
        self.assertGreaterEqual(len(payload["presets"]), 3)

        for item in payload["presets"]:
            self.assertIn("name", item)
            self.assertIn("phase", item)

        phase_order = {"create": 0, "post": 1, "work": 2}
        observed = [(item["name"], item["phase"]) for item in payload["presets"]]
        expected = sorted(observed, key=lambda pair: (phase_order.get(pair[1], 99), pair[0]))
        self.assertEqual(observed, expected)

        names = [item["name"] for item in payload["presets"]]
        self.assertEqual(len(names), len(set(names)))

    def test_preset_list_includes_bundle_and_executive_aliases(self):
        response = self.client.get("/contracts/presets/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        names = {item["name"] for item in payload["presets"]}
        self.assertIn("create.foundation", names)
        self.assertIn("post.storyline", names)
        self.assertIn("work.execution", names)
        self.assertIn("executive.summary", names)
        self.assertIn("executive.overview", names)
        self.assertIn("executive.pipeline", names)

    def test_apply_preset_accepts_bundle_alias(self):
        slide = self._create_slide("Bundle Alias")

        response = self.client.post(
            f"/contracts/slides/{slide.id}/apply-preset/",
            data={"preset": "post.storyline"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["phase_resolved"], "post")
        self.assertEqual(payload["ui"]["layout_archetype"], "journey")

    def test_apply_preset_accepts_executive_alias(self):
        slide = self._create_slide("Executive Alias")

        response = self.client.post(
            f"/contracts/slides/{slide.id}/apply-preset/",
            data={"preset": "executive.pipeline"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["phase_resolved"], "work")
        self.assertEqual(payload["ui"]["category_resolved"], "executive")
        self.assertEqual(payload["ui"]["layout_archetype"], "pipeline")

    def test_preset_bundle_list_returns_expected_shape(self):
        response = self.client.get("/contracts/preset-bundles/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn("bundles", payload)
        self.assertIsInstance(payload["bundles"], list)
        self.assertGreaterEqual(len(payload["bundles"]), 2)
        self.assertIn("bundle.foundation.triad", [item["name"] for item in payload["bundles"]])
        foundation = next(item for item in payload["bundles"] if item["name"] == "bundle.foundation.triad")
        self.assertEqual(foundation["family"], "foundation.core")
        self.assertEqual(foundation["slide_count"], 3)
        self.assertIn("phase_distribution", foundation)
        self.assertIn("layout_distribution", foundation)
        self.assertTrue(foundation["supports_inversion"])

    def test_generate_bundle_creates_slide_sequence(self):
        slide = self._create_slide("Bundle Generator")

        response = self.client.post(
            f"/contracts/slides/{slide.id}/generate-bundle/",
            data={"bundle": "bundle.foundation.triad"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["bundle"], "bundle.foundation.triad")
        self.assertEqual(payload["source_slide_id"], slide.id)
        self.assertEqual(len(payload["generated"]), 3)

        first = payload["generated"][0]["slide"]
        second = payload["generated"][1]["slide"]
        third = payload["generated"][2]["slide"]

        self.assertEqual(first["phase_resolved"], "create")
        self.assertEqual(first["ui"]["layout_archetype"], "matrix")
        self.assertEqual(second["phase_resolved"], "post")
        self.assertEqual(second["ui"]["layout_archetype"], "journey")
        self.assertEqual(third["phase_resolved"], "work")
        self.assertEqual(third["ui"]["layout_archetype"], "pipeline")

    def test_generate_bundle_supports_custom_sequence(self):
        slide = self._create_slide("Custom Bundle Generator")

        response = self.client.post(
            f"/contracts/slides/{slide.id}/generate-bundle/",
            data={
                "name": "custom.sequence.demo",
                "label": "Custom Sequence Demo",
                "family": "custom.foundation",
                "description": "User-authored bundle",
                "sequence": ["post.storyline", "work.execution"],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["bundle"], "custom.sequence.demo")
        self.assertEqual(payload["family"], "custom.foundation")
        self.assertEqual(payload["metadata"]["slide_count"], 2)
        self.assertEqual([item["slide"]["phase_resolved"] for item in payload["generated"]], ["post", "work"])

    def test_generate_bundle_supports_executive_inversion(self):
        slide = self._create_slide("Inverted Bundle Generator")

        response = self.client.post(
            f"/contracts/slides/{slide.id}/generate-bundle/",
            data={"bundle": "bundle.foundation.triad", "inversion": "executive"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["inversion"], "executive")
        self.assertEqual(
            [item["slide"]["ui"]["category_resolved"] for item in payload["generated"]],
            ["executive", "executive", "executive"],
        )

    def test_create_persisted_bundle_and_list_it(self):
        response = self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.server-side",
                "label": "Server Side Bundle",
                "family": "custom.server",
                "description": "Persisted bundle",
                "sequence": ["create.foundation", "post.storyline", "work.execution"],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

        listed = self.client.get("/contracts/preset-bundles/")
        self.assertEqual(listed.status_code, 200)
        bundles = listed.json()["bundles"]
        names = [item["name"] for item in bundles]
        self.assertIn("custom.bundle.server-side", names)
        bundle = next(item for item in bundles if item["name"] == "custom.bundle.server-side")
        self.assertEqual(bundle["owner"]["username"], self.user.username)

    def test_delete_persisted_bundle(self):
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.deletable",
                "label": "Delete Me",
                "family": "custom.server",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )
        response = self.client.delete("/contracts/preset-bundles/custom.bundle.deletable/delete/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["deleted"], "custom.bundle.deletable")

    def test_persisted_bundle_catalog_is_user_scoped(self):
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.mine",
                "label": "Mine",
                "family": "custom.user",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )

        self.client.logout()
        self.client.force_login(self.other_user)
        response = self.client.get("/contracts/preset-bundles/")
        self.assertEqual(response.status_code, 200)
        names = {item["name"] for item in response.json()["bundles"]}
        self.assertNotIn("custom.bundle.mine", names)

    def test_cannot_overwrite_other_users_bundle(self):
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.protected",
                "label": "Protected",
                "family": "custom.user",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )

        self.client.logout()
        self.client.force_login(self.other_user)
        response = self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.protected",
                "label": "Hijacked",
                "family": "custom.user",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "You do not own this bundle.")

    def test_cannot_delete_other_users_bundle(self):
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.protected-delete",
                "label": "Protected Delete",
                "family": "custom.user",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )

        self.client.logout()
        self.client.force_login(self.other_user)
        response = self.client.delete("/contracts/preset-bundles/custom.bundle.protected-delete/delete/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "You do not own this bundle.")

    def test_owner_can_update_existing_bundle(self):
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.updatable",
                "label": "Updatable",
                "family": "custom.user",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )

        response = self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.updatable",
                "label": "Updated Label",
                "family": "custom.updated",
                "sequence": ["create.foundation", "post.storyline", "work.execution"],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()["bundle"]
        self.assertEqual(payload["label"], "Updated Label")
        self.assertEqual(payload["family"], "custom.updated")
        self.assertEqual(payload["slide_count"], 3)
        self.assertEqual(payload["current_revision"]["revision_number"], 2)
        self.assertEqual(payload["revision_count"], 2)

    def test_bundle_history_endpoint_returns_revision_history(self):
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.history",
                "label": "History v1",
                "family": "custom.history",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.history",
                "label": "History v2",
                "family": "custom.history",
                "sequence": ["create.foundation", "post.storyline", "work.execution"],
            },
            content_type="application/json",
        )

        response = self.client.get("/contracts/preset-bundles/custom.bundle.history/history/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["bundle"]["current_revision"]["revision_number"], 2)
        self.assertEqual(len(payload["history"]), 2)
        self.assertEqual(payload["history"][0]["revision_number"], 2)
        self.assertEqual(payload["history"][1]["revision_number"], 1)

    def test_owner_can_share_bundle_with_view_permission(self):
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.shared-view",
                "label": "Shared View",
                "family": "custom.share",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )

        response = self.client.post(
            "/contracts/preset-bundles/custom.bundle.shared-view/shares/",
            data={"username": self.other_user.username, "permission": "view"},
            content_type="application/json",
        )
        self.assertIn(response.status_code, {200, 201})
        self.assertEqual(response.json()["share"]["permission"], "view")

        self.client.logout()
        self.client.force_login(self.other_user)
        catalog = self.client.get("/contracts/preset-bundles/")
        self.assertEqual(catalog.status_code, 200)
        names = {item["name"] for item in catalog.json()["bundles"]}
        self.assertIn("custom.bundle.shared-view", names)

    def test_view_collaborator_cannot_edit_bundle(self):
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.view-only",
                "label": "View Only",
                "family": "custom.share",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )
        self.client.post(
            "/contracts/preset-bundles/custom.bundle.view-only/shares/",
            data={"username": self.other_user.username, "permission": "view"},
            content_type="application/json",
        )

        self.client.logout()
        self.client.force_login(self.other_user)
        response = self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.view-only",
                "label": "Attempted Edit",
                "family": "custom.share",
                "sequence": ["create.foundation", "post.storyline", "work.execution"],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "You do not have edit access to this bundle.")

    def test_edit_collaborator_can_update_bundle(self):
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.editable-share",
                "label": "Editable Share",
                "family": "custom.share",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )
        self.client.post(
            "/contracts/preset-bundles/custom.bundle.editable-share/shares/",
            data={"username": self.other_user.username, "permission": "edit"},
            content_type="application/json",
        )

        self.client.logout()
        self.client.force_login(self.other_user)
        response = self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.editable-share",
                "label": "Edited By Collaborator",
                "family": "custom.share",
                "sequence": ["create.foundation", "post.storyline", "work.execution"],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["bundle"]["label"], "Edited By Collaborator")
        self.assertEqual(response.json()["bundle"]["access_role"], "edit")

    def test_bundle_compare_endpoint_returns_sequence_and_field_changes(self):
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.compare",
                "label": "Compare v1",
                "family": "custom.compare",
                "sequence": ["create.foundation", "post.storyline", "work.execution"],
            },
            content_type="application/json",
        )
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.compare",
                "label": "Compare v2",
                "family": "custom.compare.updated",
                "sequence": ["post.storyline", "work.execution"],
            },
            content_type="application/json",
        )

        response = self.client.get("/contracts/preset-bundles/custom.bundle.compare/compare/?from=1&to=2")
        self.assertEqual(response.status_code, 200)
        payload = response.json()["compare"]
        self.assertTrue(payload["changes"]["label_changed"])
        self.assertTrue(payload["changes"]["family_changed"])
        self.assertEqual(payload["sequence"]["removed"], ["create.foundation"])
        self.assertEqual(payload["sequence"]["added"], [])

    def test_bundle_rollback_creates_new_revision(self):
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.rollback",
                "label": "Rollback v1",
                "family": "custom.rollback",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.rollback",
                "label": "Rollback v2",
                "family": "custom.rollback",
                "sequence": ["create.foundation", "post.storyline", "work.execution"],
            },
            content_type="application/json",
        )

        response = self.client.post(
            "/contracts/preset-bundles/custom.bundle.rollback/rollback/",
            data={"revision_number": 1},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["rolled_back_to"], 1)
        self.assertEqual(payload["new_revision"]["revision_number"], 3)
        self.assertEqual(payload["bundle"]["sequence"], ["create.foundation", "post.storyline"])

    def test_bundle_tags_can_be_created_and_repointed(self):
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.tags",
                "label": "Tags v1",
                "family": "custom.tags",
                "sequence": ["create.foundation", "post.storyline"],
            },
            content_type="application/json",
        )
        self.client.post(
            "/contracts/preset-bundles/create/",
            data={
                "name": "custom.bundle.tags",
                "label": "Tags v2",
                "family": "custom.tags",
                "sequence": ["create.foundation", "post.storyline", "work.execution"],
            },
            content_type="application/json",
        )

        create_tag = self.client.post(
            "/contracts/preset-bundles/custom.bundle.tags/tags/",
            data={"name": "stable", "revision_number": 1},
            content_type="application/json",
        )
        self.assertEqual(create_tag.status_code, 201)
        self.assertEqual(create_tag.json()["tag"]["revision_number"], 1)

        move_tag = self.client.post(
            "/contracts/preset-bundles/custom.bundle.tags/tags/",
            data={"name": "stable", "revision_number": 2},
            content_type="application/json",
        )
        self.assertEqual(move_tag.status_code, 200)
        self.assertEqual(move_tag.json()["tag"]["revision_number"], 2)

    def test_generate_bundle_preview_mode_does_not_persist_slides(self):
        slide = self._create_slide("Preview Mode Generator")
        before_count = Slide.objects.count()

        response = self.client.post(
            f"/contracts/slides/{slide.id}/generate-bundle/",
            data={"bundle": "bundle.foundation.triad", "persist_generated": False},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["persist_generated"])
        self.assertEqual(Slide.objects.count(), before_count)

    def test_generate_bundle_rejects_unknown_sequence_member(self):
        slide = self._create_slide("Invalid Sequence Generator")

        response = self.client.post(
            f"/contracts/slides/{slide.id}/generate-bundle/",
            data={
                "name": "custom.bundle.invalid",
                "label": "Invalid",
                "family": "custom.invalid",
                "sequence": ["create.foundation", "missing.preset"],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unknown preset in sequence", response.json()["detail"])

    def test_generate_bundle_rejects_consecutive_same_phase_steps(self):
        slide = self._create_slide("Invalid Phase Sequence Generator")

        response = self.client.post(
            f"/contracts/slides/{slide.id}/generate-bundle/",
            data={
                "name": "custom.bundle.invalid-phases",
                "label": "Invalid Phases",
                "family": "custom.invalid",
                "sequence": ["create.foundation", "create.red.math"],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("consecutive presets in the same phase", response.json()["detail"])

    def test_slide_detail_returns_expected_json_shape(self):
        slide = self._create_slide("Slide Detail Shape")

        response = self.client.get(f"/contracts/slides/{slide.id}/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["id"], slide.id)
        self.assertIn("title", payload)
        self.assertIn("phase", payload)
        self.assertIn("phase_resolved", payload)
        self.assertIn("color_primary", payload)
        self.assertIn("metaphor", payload)
        self.assertIn("mlas", payload)
        self.assertIn("dewey", payload)
        self.assertIn("industry", payload)
        self.assertIn("ui", payload)
        self.assertIn("applied_preset", payload)

        self.assertIn("subject", payload["mlas"])
        self.assertIn("branch", payload["mlas"])
        self.assertIn("term", payload["mlas"])
        self.assertIn("meta", payload["mlas"])

        self.assertIn("code", payload["dewey"])
        self.assertIn("nav_group", payload["dewey"])

        self.assertIn("super_sector", payload["industry"])
        self.assertIn("sector", payload["industry"])
        self.assertIn("group", payload["industry"])
        self.assertIn("sub_industry", payload["industry"])
        self.assertIn("page_signature", payload["industry"])

        self.assertIn("category", payload["ui"])
        self.assertIn("category_resolved", payload["ui"])
        self.assertIn("layout_archetype", payload["ui"])
        self.assertIn("component_pack", payload["ui"])

    def test_slide_detail_missing_slide_returns_404_shape(self):
        response = self.client.get("/contracts/slides/999999/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Slide not found."})

    def test_apply_preset_requires_authentication(self):
        slide = self._create_slide("Apply Preset Auth")
        self.client.logout()

        response = self.client.post(
            f"/contracts/slides/{slide.id}/apply-preset/",
            data={"preset": self.post_preset.name},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "Authentication required."})

    def test_apply_preset_invalid_json_returns_400_shape(self):
        slide = self._create_slide("Apply Preset Invalid JSON")

        response = self.client.post(
            f"/contracts/slides/{slide.id}/apply-preset/",
            data="{invalid-json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Invalid JSON body."})

    def test_apply_preset_missing_name_returns_400_shape(self):
        slide = self._create_slide("Apply Preset Missing Name")

        response = self.client.post(
            f"/contracts/slides/{slide.id}/apply-preset/",
            data={},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "preset or preset_name is required."})

    def test_apply_preset_unknown_preset_returns_404_shape(self):
        slide = self._create_slide("Apply Preset Missing Preset")

        response = self.client.post(
            f"/contracts/slides/{slide.id}/apply-preset/",
            data={"preset": "does.not.exist"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Preset not found."})

    def test_apply_preset_happy_path_returns_expected_json_shape(self):
        slide = self._create_slide("Apply Preset Shape")

        response = self.client.post(
            f"/contracts/slides/{slide.id}/apply-preset/",
            data={"preset": self.post_preset.name},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["id"], slide.id)
        self.assertIn("title", payload)
        self.assertIn("phase", payload)
        self.assertIn("phase_resolved", payload)
        self.assertIn("color_primary", payload)
        self.assertIn("metaphor", payload)
        self.assertIn("mlas", payload)
        self.assertIn("dewey", payload)
        self.assertIn("industry", payload)
        self.assertIn("ui", payload)
        self.assertIn("applied_preset", payload)
