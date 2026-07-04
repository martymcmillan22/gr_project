from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase


class ImportGicsReferenceCommandTests(SimpleTestCase):
    def test_import_gics_reference_rejects_placeholder_path(self):
        with self.assertRaises(CommandError) as ctx:
            call_command("import_gics_reference", "--file", "/Users/you/path/gics.csv")

        self.assertIn("placeholder path", str(ctx.exception).lower())
