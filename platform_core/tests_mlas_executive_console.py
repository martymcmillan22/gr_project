from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from platform_core.models import MLASClassificationRecord
from platform_reference.models import PlatformReferenceGICSReferenceSchema
from platform_reference.models import PlatformReferenceNAICSReferenceSchema


class ClassificationExecutiveConsoleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.staff_user = user_model.objects.create_user(
            username="classification_staff",
            email="classification_staff@example.com",
            password="password12345",
            is_staff=True,
        )
        cls.normal_user = user_model.objects.create_user(
            username="classification_viewer",
            email="classification_viewer@example.com",
            password="password12345",
        )
        cls.reviewer = user_model.objects.create_user(
            username="classification_reviewer",
            email="classification_reviewer@example.com",
            password="password12345",
            is_staff=True,
        )

    def _record_payload(self, record_id: str, **overrides):
        payload = {
            "record_id": record_id,
            "source_name_raw": "Source",
            "target_layer": MLASClassificationRecord.TARGET_TERM,
            "mlas_subject_code": "MATH",
            "mlas_branch_code": "SACP",
            "mlas_term_code": "CNIC",
            "dewey_code": "630",
            "algorithm_1_score": 0.9,
            "algorithm_2_score": 0.9,
            "algorithm_3_score": 0.9,
            "algorithm_4_score": 0.9,
            "confidence_overall": 0.92,
            "review_status": MLASClassificationRecord.REVIEW_CANDIDATE,
        }
        payload.update(overrides)
        return payload

    def test_requires_staff_access(self):
        self.client.force_login(self.normal_user)
        response = self.client.get("/contracts/classification/executive/")
        self.assertEqual(response.status_code, 403)

    def test_empty_dataset_reports_blocked_readiness(self):
        self.client.force_login(self.staff_user)
        response = self.client.get("/contracts/classification/executive/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_records"], 0)
        self.assertEqual(response.context["training_readiness"]["status"], "Blocked")

        heat = response.context["training_readiness_heat"]
        self.assertEqual(heat["score"], 0)
        self.assertEqual(heat["band"], "red")
        self.assertEqual(heat["label"], "Blocked")
        self.assertEqual(response.context["reference_sync"]["gics"]["source_status"], "missing")

    def test_returns_kpis_for_staff(self):
        PlatformReferenceNAICSReferenceSchema.objects.create(code="111110", title="Soybean Farming", sector_code="11", source_version="NAICS-2022")
        PlatformReferenceGICSReferenceSchema.objects.create(
            code="10101010",
            name="Energy Equipment and Services",
            level=PlatformReferenceGICSReferenceSchema.LEVEL_SUB_INDUSTRY,
            source_version="GICS-LICENSED",
        )

        MLASClassificationRecord.objects.create(
            **self._record_payload(
                "EXEC-001",
                review_status=MLASClassificationRecord.REVIEW_APPROVED,
                reviewer=self.reviewer,
                reviewed_at=timezone.now(),
            )
        )
        MLASClassificationRecord.objects.create(
            **self._record_payload(
                "EXEC-002",
                review_status=MLASClassificationRecord.REVIEW_CANDIDATE,
                confidence_overall=0.7,
                mlas_term_code="CALE",
                dewey_code="",
                gics_sub_industry_code="10101010",
            )
        )
        MLASClassificationRecord.objects.create(
            **self._record_payload(
                "EXEC-003",
                review_status=MLASClassificationRecord.REVIEW_APPROVED,
                reviewer=self.reviewer,
                reviewed_at=timezone.now(),
                mlas_term_code="CNIC",
                basetrue_label="DupLabel",
            )
        )
        MLASClassificationRecord.objects.create(
            **self._record_payload(
                "EXEC-004",
                review_status=MLASClassificationRecord.REVIEW_APPROVED,
                reviewer=self.reviewer,
                reviewed_at=timezone.now(),
                mlas_term_code="CALE",
                basetrue_label="DupLabel",
            )
        )

        # Force edge-case conflicts by bypassing full_clean validations.
        MLASClassificationRecord.objects.filter(record_id="EXEC-003").update(
            dewey_code="",
            gics_sub_industry_code="",
            naics_code_6="",
        )
        MLASClassificationRecord.objects.filter(record_id="EXEC-002").update(mlas_meta_term_code="DDNC")

        MLASClassificationRecord.objects.create(
            **self._record_payload(
                "EXEC-005",
                target_layer=MLASClassificationRecord.TARGET_META,
                review_status=MLASClassificationRecord.REVIEW_CANDIDATE,
                mlas_term_code="DMDA",
                dewey_code="650",
                gics_sub_industry_code="",
                naics_code_6="111110",
                mlas_meta_term_code="META1",
            )
        )
        MLASClassificationRecord.objects.filter(record_id="EXEC-005").update(mlas_meta_term_code="")

        self.client.force_login(self.staff_user)
        response = self.client.get("/contracts/classification/executive/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "platform_core/classification_executive.html")
        self.assertEqual(response.context["total_records"], 5)
        self.assertEqual(response.context["approved_term_count"], 2)
        self.assertEqual(response.context["confidence_bands"]["green"], 4)
        self.assertEqual(response.context["confidence_bands"]["red"], 1)
        self.assertEqual(response.context["reviewer_queue"]["candidate"], 2)
        self.assertEqual(response.context["external_alignment"]["gics"], 1)
        self.assertEqual(response.context["training_readiness"]["status"], "In Progress")
        self.assertEqual(response.context["reference_sync"]["naics"]["count"], 1)
        self.assertEqual(response.context["reference_sync"]["gics"]["count"], 1)
        self.assertEqual(response.context["reference_sync"]["naics"]["matched"], 1)
        self.assertEqual(response.context["reference_sync"]["gics"]["matched"], 1)
        self.assertEqual(response.context["reference_sync"]["gics"]["source_status"], "licensed")

        links = response.context["admin_links"]
        self.assertIn("/admin/platform_core/mlasclassificationrecord/", links["all"])
        self.assertTrue(
            "/admin/platform_core/naicsreference/" in links["naics_reference"]
            or "/admin/platform_reference/naicsreference/" in links["naics_reference"]
            or "/admin/platform_reference/platformreferencenaicsreferenceschema/" in links["naics_reference"]
        )
        self.assertTrue(
            "/admin/platform_core/gicsreference/" in links["gics_reference"]
            or "/admin/platform_reference/gicsreference/" in links["gics_reference"]
            or "/admin/platform_reference/platformreferencegicsreferenceschema/" in links["gics_reference"]
        )
        self.assertIn("validation_band=red", links["red_band"])
        self.assertIn("review_status__exact=candidate", links["candidate_queue"])
        self.assertIn("external_alignment=missing", links["missing_external"])
        self.assertIn("semantic_conflict=duplicate_term", links["conflict_duplicate_term"])
        self.assertIn("semantic_conflict=duplicate_label", links["conflict_duplicate_label"])
        self.assertIn("semantic_conflict=approved_missing_external", links["conflict_approved_missing_external"])
        self.assertIn("semantic_conflict=term_with_meta", links["conflict_term_with_meta"])
        self.assertIn("semantic_conflict=meta_missing_meta", links["conflict_meta_missing_meta"])
        self.assertIn("validation_band=red", links["heat_red_band"])
        self.assertIn("semantic_conflict=duplicate_term", links["heat_conflicts"])
        self.assertIn("review_status__exact=candidate", links["heat_candidate_backlog"])
        self.assertIn("external_alignment=missing", links["heat_missing_external"])

        conflicts = response.context["semantic_conflicts"]
        self.assertEqual(conflicts["duplicate_term"], 2)
        self.assertEqual(conflicts["duplicate_label"], 2)
        self.assertEqual(conflicts["approved_missing_external"], 1)
        self.assertEqual(conflicts["term_with_meta"], 1)
        self.assertEqual(conflicts["meta_missing_meta"], 1)

        heat = response.context["training_readiness_heat"]
        self.assertEqual(heat["score"], 65)
        self.assertEqual(heat["band"], "yellow")
        self.assertEqual(heat["label"], "Caution")
        self.assertEqual(heat["blockers"]["red_band_count"], 1)
        self.assertEqual(heat["blockers"]["semantic_conflict_total"], 7)
        self.assertEqual(heat["blockers"]["candidate_backlog"], 2)
        self.assertEqual(heat["blockers"]["missing_external_count"], 1)
        self.assertEqual(heat["penalties"]["red_band"], 6)
        self.assertEqual(heat["penalties"]["semantic_conflicts"], 21)
        self.assertEqual(heat["penalties"]["candidate_backlog"], 4)
        self.assertEqual(heat["penalties"]["missing_external"], 4)

    def test_heat_cannot_be_green_before_term_goal(self):
        MLASClassificationRecord.objects.create(
            **self._record_payload(
                "EXEC-GATE-001",
                review_status=MLASClassificationRecord.REVIEW_APPROVED,
                reviewer=self.reviewer,
                reviewed_at=timezone.now(),
                mlas_term_code="T001",
                confidence_overall=0.95,
            )
        )

        self.client.force_login(self.staff_user)
        response = self.client.get("/contracts/classification/executive/")

        self.assertEqual(response.status_code, 200)
        heat = response.context["training_readiness_heat"]
        self.assertEqual(response.context["approved_term_count"], 1)
        self.assertEqual(heat["score"], 100)
        self.assertEqual(heat["band"], "yellow")
        self.assertEqual(heat["label"], "Caution")

    def test_gics_demo_source_status_when_non_licensed_data_loaded(self):
        PlatformReferenceGICSReferenceSchema.objects.create(
            code="10101010",
            name="Demo Sub Industry",
            level=PlatformReferenceGICSReferenceSchema.LEVEL_SUB_INDUSTRY,
            source_version="DEMO-GICS-UNLICENSED",
        )

        self.client.force_login(self.staff_user)
        response = self.client.get("/contracts/classification/executive/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["reference_sync"]["gics"]["source_status"], "demo")
