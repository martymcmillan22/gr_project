from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from platform_core.models import MLASClassificationRecord


class MLASClassificationRecordTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.reviewer = user_model.objects.create_user(
            username="mlas_reviewer",
            email="mlas_reviewer@example.com",
            password="password12345",
        )

    def _base_payload(self):
        return {
            "record_id": "REC-0001",
            "source_name_raw": "Applied Crop Scheduling",
            "source_description_raw": "Alignment sample",
            "target_layer": MLASClassificationRecord.TARGET_TERM,
            "mlas_subject_code": "MATH",
            "dewey_code": "630",
            "algorithm_1_score": 0.8,
            "algorithm_2_score": 0.7,
            "algorithm_3_score": 0.9,
            "algorithm_4_score": 0.6,
            "confidence_overall": 0.82,
            "review_status": MLASClassificationRecord.REVIEW_CANDIDATE,
        }

    def test_candidate_row_persists_and_calculates_consensus(self):
        record = MLASClassificationRecord.objects.create(**self._base_payload())
        self.assertEqual(record.algorithm_consensus_score, 0.75)

    def test_requires_external_link(self):
        payload = self._base_payload()
        payload["dewey_code"] = ""
        payload["gics_sub_industry_code"] = ""
        payload["naics_code_6"] = ""

        with self.assertRaises(ValidationError):
            MLASClassificationRecord.objects.create(**payload)

    def test_approved_row_requires_branch_term_and_reviewer(self):
        payload = self._base_payload()
        payload["review_status"] = MLASClassificationRecord.REVIEW_APPROVED

        with self.assertRaises(ValidationError):
            MLASClassificationRecord.objects.create(**payload)

    def test_approved_row_with_required_fields_passes(self):
        payload = self._base_payload()
        payload.update(
            {
                "review_status": MLASClassificationRecord.REVIEW_APPROVED,
                "mlas_branch_code": "SACP",
                "mlas_term_code": "CNIC",
                "reviewer": self.reviewer,
                "reviewed_at": timezone.now(),
            }
        )

        record = MLASClassificationRecord.objects.create(**payload)
        self.assertEqual(record.review_status, MLASClassificationRecord.REVIEW_APPROVED)

    def test_meta_target_requires_meta_term_code(self):
        payload = self._base_payload()
        payload["target_layer"] = MLASClassificationRecord.TARGET_META

        with self.assertRaises(ValidationError):
            MLASClassificationRecord.objects.create(**payload)

    def test_term_target_rejects_meta_term_code(self):
        payload = self._base_payload()
        payload["mlas_meta_term_code"] = "DDNC"

        with self.assertRaises(ValidationError):
            MLASClassificationRecord.objects.create(**payload)
