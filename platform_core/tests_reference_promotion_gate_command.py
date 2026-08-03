import os
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from platform_reference.models import PlatformReferenceGICSReferenceSchema


class ReferencePromotionGateCommandTests(TestCase):
    @override_settings(DEBUG=True)
    def test_skips_in_non_production_even_with_demo_data(self):
        PlatformReferenceGICSReferenceSchema.objects.create(
            code="10101010",
            name="Demo Sub Industry",
            level=PlatformReferenceGICSReferenceSchema.LEVEL_SUB_INDUSTRY,
            source_version="DEMO-GICS-UNLICENSED",
        )

        output = StringIO()
        with mock.patch.dict(os.environ, {"DJANGO_ENV": ""}, clear=False):
            call_command("check_reference_promotion_gate", stdout=output)

        self.assertIn("Promotion gate skipped", output.getvalue())

    @override_settings(DEBUG=False)
    def test_fails_in_production_when_gics_is_demo(self):
        PlatformReferenceGICSReferenceSchema.objects.create(
            code="10101010",
            name="Demo Sub Industry",
            level=PlatformReferenceGICSReferenceSchema.LEVEL_SUB_INDUSTRY,
            source_version="DEMO-GICS-UNLICENSED",
        )

        with self.assertRaises(CommandError) as ctx:
            call_command("check_reference_promotion_gate")

        self.assertIn("requires licensed gics", str(ctx.exception).lower())

    @override_settings(DEBUG=False)
    def test_passes_in_production_with_licensed_gics(self):
        PlatformReferenceGICSReferenceSchema.objects.create(
            code="10101010",
            name="Licensed Sub Industry",
            level=PlatformReferenceGICSReferenceSchema.LEVEL_SUB_INDUSTRY,
            source_version="GICS-LICENSED-2026",
        )

        output = StringIO()
        call_command("check_reference_promotion_gate", stdout=output)

        self.assertIn("Promotion gate passed", output.getvalue())

    def test_enforce_production_flag_blocks_when_missing(self):
        with self.assertRaises(CommandError) as ctx:
            call_command("check_reference_promotion_gate", "--enforce-production")

        self.assertIn("current status: missing", str(ctx.exception).lower())