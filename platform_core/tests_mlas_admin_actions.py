from django.contrib import admin
from django.test import RequestFactory, TestCase

from platform_core.admin import MLASClassificationRecordAdmin
from platform_core.models import MLASClassificationRecord


class MLASClassificationRecordAdminActionsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.model_admin = MLASClassificationRecordAdmin(MLASClassificationRecord, admin.site)

    def _create_record(self, record_id: str, review_status: str):
        return MLASClassificationRecord.objects.create(
            record_id=record_id,
            source_name_raw="Sample",
            target_layer=MLASClassificationRecord.TARGET_TERM,
            mlas_subject_code="MATH",
            mlas_branch_code="SACP",
            mlas_term_code="CNIC",
            dewey_code="630",
            algorithm_1_score=0.8,
            algorithm_2_score=0.8,
            algorithm_3_score=0.6,
            algorithm_4_score=0.6,
            confidence_overall=0.78,
            review_status=review_status,
        )

    def test_promote_to_candidate_action(self):
        record = self._create_record("ADM-001", MLASClassificationRecord.REVIEW_DRAFT)

        self.model_admin.promote_to_candidate(
            self.factory.get("/admin/"),
            MLASClassificationRecord.objects.filter(id=record.id),
        )

        record.refresh_from_db()
        self.assertEqual(record.review_status, MLASClassificationRecord.REVIEW_CANDIDATE)

    def test_mark_rejected_action(self):
        record = self._create_record("ADM-002", MLASClassificationRecord.REVIEW_CANDIDATE)

        self.model_admin.mark_rejected(
            self.factory.get("/admin/"),
            MLASClassificationRecord.objects.filter(id=record.id),
        )

        record.refresh_from_db()
        self.assertEqual(record.review_status, MLASClassificationRecord.REVIEW_REJECTED)

    def test_recompute_consensus_and_reason_action(self):
        record = self._create_record("ADM-003", MLASClassificationRecord.REVIEW_CANDIDATE)
        MLASClassificationRecord.objects.filter(id=record.id).update(
            algorithm_consensus_score=0.0,
            confidence_reason="",
            algorithm_1_score=1.0,
            algorithm_2_score=1.0,
            algorithm_3_score=0.6,
            algorithm_4_score=0.6,
            confidence_overall=0.92,
        )

        self.model_admin.recompute_consensus_and_reason(
            self.factory.get("/admin/"),
            MLASClassificationRecord.objects.filter(id=record.id),
        )

        record.refresh_from_db()
        self.assertEqual(record.algorithm_consensus_score, 0.8)
        self.assertIn("algorithm_consensus=0.80", record.confidence_reason)
        self.assertIn("good alignment with minor ambiguity", record.confidence_reason)
