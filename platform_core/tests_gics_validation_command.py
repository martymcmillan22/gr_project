import csv
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase


class ValidateGicsReferenceCommandTests(SimpleTestCase):
    def _write_csv(self, headers, rows):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8", newline="")
        with tmp as fh:
            writer = csv.DictWriter(fh, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        path = Path(tmp.name)
        self.addCleanup(lambda: path.exists() and path.unlink())
        return path

    def test_validate_gics_reference_passes_for_valid_hierarchy(self):
        headers = ["code", "name", "level", "parent_code", "description", "source_version"]
        rows = [
            {
                "code": "10",
                "name": "Energy",
                "level": "sector",
                "parent_code": "",
                "description": "Sector",
                "source_version": "Licensed-GICS-20260630",
            },
            {
                "code": "1010",
                "name": "Energy Equipment and Services",
                "level": "industry_group",
                "parent_code": "10",
                "description": "Industry group",
                "source_version": "Licensed-GICS-20260630",
            },
            {
                "code": "101010",
                "name": "Energy Equipment & Services",
                "level": "industry",
                "parent_code": "1010",
                "description": "Industry",
                "source_version": "Licensed-GICS-20260630",
            },
            {
                "code": "10101010",
                "name": "Oil & Gas Equipment & Services",
                "level": "sub_industry",
                "parent_code": "101010",
                "description": "Sub-industry",
                "source_version": "Licensed-GICS-20260630",
            },
        ]
        file_path = self._write_csv(headers, rows)

        output = StringIO()
        call_command("validate_gics_reference", "--file", str(file_path), stdout=output)

        self.assertIn("GICS CSV validation passed", output.getvalue())

    def test_validate_gics_reference_fails_on_missing_columns(self):
        headers = ["code", "name", "level"]
        rows = [{"code": "10", "name": "Energy", "level": "sector"}]
        file_path = self._write_csv(headers, rows)

        with self.assertRaises(CommandError) as ctx:
            call_command("validate_gics_reference", "--file", str(file_path))

        self.assertIn("missing required columns", str(ctx.exception).lower())

    def test_validate_gics_reference_fails_on_invalid_level(self):
        headers = ["code", "name", "level", "parent_code", "description", "source_version"]
        rows = [
            {
                "code": "10",
                "name": "Energy",
                "level": "bad_level",
                "parent_code": "",
                "description": "Sector",
                "source_version": "Licensed-GICS-20260630",
            }
        ]
        file_path = self._write_csv(headers, rows)

        with self.assertRaises(CommandError) as ctx:
            call_command("validate_gics_reference", str(file_path))

        self.assertIn("unsupported gics level", str(ctx.exception).lower())

    def test_validate_gics_reference_fails_when_parent_missing_for_non_sector(self):
        headers = ["code", "name", "level", "parent_code", "description", "source_version"]
        rows = [
            {
                "code": "1010",
                "name": "Energy Equipment and Services",
                "level": "industry_group",
                "parent_code": "",
                "description": "Industry group",
                "source_version": "Licensed-GICS-20260630",
            }
        ]
        file_path = self._write_csv(headers, rows)

        with self.assertRaises(CommandError) as ctx:
            call_command("validate_gics_reference", str(file_path))

        self.assertIn("parent_code is required", str(ctx.exception).lower())

    def test_validate_gics_reference_rejects_placeholder_path(self):
        with self.assertRaises(CommandError) as ctx:
            call_command("validate_gics_reference", "--file", "/Users/you/path/gics.csv")

        self.assertIn("placeholder path", str(ctx.exception).lower())