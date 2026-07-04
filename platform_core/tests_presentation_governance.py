from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from platform_core.presentation_mdx import (
    _default_registry_presets,
    _parse_slide,
    _validate_documentation_sync,
    _validate_generation_rules,
    _validate_metadata_contract,
    _validate_preset_contract,
    sync_presentation_blueprints,
)


def _write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _valid_readme_text():
    return "\n".join(
        [
            "# Presentation MDX Pipeline",
            "summary.presets",
            "generatedSlidePresets",
            "generatedSlideRegistryMeta.presets",
            "phase2_semantic_sprint_checklist.md",
        ]
    )


def _valid_checklist_text():
    return "\n".join(
        [
            "# Phase 2 Semantic Sprint Checklist",
            "Day 6 - Integrate Semantic Layer",
            "Day 8 - Add Semantic Coverage Linter",
            "Day 9 - Browser Regression and Scripted Validation",
        ]
    )


def _valid_blueprint_slide_text():
    return """---
category: blueprint
labels: baseline, reference
---

# Blueprint Slide

<LayoutGrid columns=\"2\" gap=\"16\" />
<Panel title=\"Main\" tone=\"primary\" />
<Quadrant label=\"Q1\" emphasis=\"high\" />
<ComponentPreview component=\"DashboardCard\" status=\"ready\" />
"""


def _valid_operations_slide_text():
    return """---
category: operations
labels: risk, mitigation
---

# Operations Slide

<Quadrant label=\"Q1\" emphasis=\"high\" />
<ComponentPreview component=\"RiskIntakePanel\" status=\"ready\" />
"""


def _valid_customer_slide_text():
    return """---
category: customer
labels: journey, lifecycle
---

# Customer Slide

<LayoutGrid columns=\"2\" gap=\"12\" />
<ComponentPreview component=\"JourneyPanel\" status=\"ready\" />
"""


def _valid_delivery_slide_text():
    return """---
category: delivery
labels: reliability, incidents
---

# Delivery Slide

<LayoutGrid columns=\"2\" gap=\"12\" />
<ComponentPreview component=\"ControlTower\" status=\"ready\" />
"""


class PresentationGovernanceValidatorTests(SimpleTestCase):
    def test_metadata_contract_enforces_required_category_and_labels(self):
        with TemporaryDirectory() as tmp:
            slide_path = Path(tmp) / "missing_meta.mdx"
            _write_text(
                slide_path,
                """# Missing Meta\n\n<Panel title=\"Ops\" tone=\"primary\" />\n""",
            )

            blueprint = _parse_slide(slide_path)
            errors, warnings = _validate_metadata_contract([blueprint])

            self.assertTrue(any("invalid category" in item for item in errors))
            self.assertTrue(any("requires at least one label" in item for item in errors))
            self.assertEqual(warnings, [])

    def test_generation_rule_enforcement_flags_missing_required_tags(self):
        with TemporaryDirectory() as tmp:
            slide_path = Path(tmp) / "ops_slide.mdx"
            _write_text(
                slide_path,
                """---
category: operations
labels: risk, mitigation
---

# Ops Slide

<Panel title=\"Only Panel\" tone=\"warning\" />
""",
            )

            blueprint = _parse_slide(slide_path)
            errors, _warnings = _validate_generation_rules([blueprint])

            self.assertTrue(any("Missing required tags" in item for item in errors))

    def test_preset_contract_enforces_structure_and_reference_integrity(self):
        slides = [
            {
                "id": "risk-operations-matrix",
                "title": "Risk Operations Matrix",
                "route": "/homepage/slides/risk-operations-matrix",
                "category": "operations",
                "source_file": "risk-operations-matrix.mdx",
                "preview_components": ["RiskIntakePanel"],
                "tag_count": 14,
                "tags_by_type": {"ComponentPreview": 6, "Quadrant": 4},
                "component_name": "RiskOperationsMatrixSlideGenerated",
                "page_name": "RiskOperationsMatrixPageGenerated",
            }
        ]
        presets = _default_registry_presets() + [
            {
                "id": "bad_preset",
                "name": "Bad Preset",
                "quick_switch": False,
                "filters": {
                    "tag_type": "all",
                    "tag_count_band": "all",
                    "category": "unknown_category",
                    "component_name": "all",
                    "page_name": "all",
                },
                "sort_order": "title_asc",
                "grouping_mode": "none",
                "search_query": "",
            }
        ]

        errors, _warnings = _validate_preset_contract(slides, presets)

        self.assertTrue(any("unknown category 'unknown_category'" in item for item in errors))

    def test_readme_and_checklist_governance_markers_are_enforced(self):
        with TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            readme_path = base_dir / "docs" / "architecture" / "presentation" / "README.md"
            checklist_path = (
                base_dir / "docs" / "architecture" / "presentation" / "phase2_semantic_sprint_checklist.md"
            )
            _write_text(readme_path, "# Presentation\nmissing required markers\n")
            _write_text(checklist_path, "# Checklist\nmissing required markers\n")

            errors, _warnings = _validate_documentation_sync(base_dir, _default_registry_presets())

            self.assertGreaterEqual(len(errors), 2)
            self.assertTrue(any("README governance mismatch" in item for item in errors))
            self.assertTrue(any("Checklist governance mismatch" in item for item in errors))


class PresentationSyncGovernanceEnforcementTests(SimpleTestCase):
    def _write_required_docs(self, base_dir: Path):
        readme_path = base_dir / "docs" / "architecture" / "presentation" / "README.md"
        checklist_path = (
            base_dir / "docs" / "architecture" / "presentation" / "phase2_semantic_sprint_checklist.md"
        )
        _write_text(readme_path, _valid_readme_text())
        _write_text(checklist_path, _valid_checklist_text())

    def test_sync_fails_when_slide_metadata_contract_is_invalid(self):
        with TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            self._write_required_docs(base_dir)
            slides_dir = base_dir / "docs" / "architecture" / "presentation" / "slides"
            _write_text(
                slides_dir / "bad_slide.mdx",
                """---
category: unknown
labels:
---

# Bad Slide

<Panel title=\"Broken\" tone=\"danger\" />
""",
            )

            with self.assertRaisesRegex(ValueError, "Presentation contract validation failed"):
                sync_presentation_blueprints(base_dir)

    def test_sync_succeeds_with_valid_contract_and_returns_summary(self):
        with TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            self._write_required_docs(base_dir)
            slides_dir = base_dir / "docs" / "architecture" / "presentation" / "slides"
            _write_text(slides_dir / "ui_blueprint_standard.mdx", _valid_blueprint_slide_text())
            _write_text(slides_dir / "risk_ops.mdx", _valid_operations_slide_text())
            _write_text(slides_dir / "customer_journey.mdx", _valid_customer_slide_text())
            _write_text(slides_dir / "delivery_control.mdx", _valid_delivery_slide_text())

            summary = sync_presentation_blueprints(base_dir)

            self.assertEqual(summary["slide_count"], 4)
            self.assertIn("validation_warnings", summary)
            self.assertTrue((base_dir / "docs" / "architecture" / "presentation" / "ui" / "generated" / "manifest.json").exists())
            self.assertTrue((base_dir / "frontend_homepage" / "src" / "ui" / "generated" / "index.js").exists())
