import json
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_BLUEPRINT_TAGS = {"LayoutGrid", "Panel", "Quadrant", "ComponentPreview"}
ALLOWED_SLIDE_CATEGORIES = {"blueprint", "operations", "customer", "delivery", "risk", "admin"}
PRESET_ALLOWED_TAG_COUNT_BANDS = {"all", "0-10", "11-14", "15+"}
PRESET_ALLOWED_SORT_ORDERS = {"title_asc", "title_desc", "tag_desc", "tag_asc", "category_asc"}
PRESET_ALLOWED_GROUPING_MODES = {"none", "category", "tag_type"}
SORT_KEYS_WITHOUT_EXPLICIT_TIEBREAK = {"tag_desc", "tag_asc", "title_desc"}
REQUIRED_README_MARKERS = [
    "summary.presets",
    "sync_presentation_ui",
    "phase2_semantic_sprint_checklist.md",
    "Execution board",
]
REQUIRED_CHECKLIST_MARKERS = [
    "Day 1 - Lock Semantic Contract",
    "Day 10 - Freeze and Release Gate",
    "Gate D: No Phase 3 start without explicit go decision.",
]
GENERATION_RULES_BY_CATEGORY = {
    "blueprint": {"LayoutGrid", "Panel", "Quadrant", "ComponentPreview"},
    "operations": {"Quadrant", "ComponentPreview"},
    "customer": {"LayoutGrid", "ComponentPreview"},
    "delivery": {"LayoutGrid", "ComponentPreview"},
    "risk": {"Quadrant", "ComponentPreview"},
    "admin": {"Panel", "ComponentPreview"},
}
TAG_PATTERN = re.compile(
    r"<(?P<tag>LayoutGrid|Panel|Quadrant|ComponentPreview)\b(?P<attrs>[^>]*)/?>",
    re.MULTILINE,
)
ATTR_PATTERN = re.compile(r"([a-zA-Z_][\w-]*)\s*=\s*\"([^\"]*)\"")


def _default_registry_presets():
    return [
        {
            "id": "operations_view",
            "name": "Operations View",
            "quick_switch": True,
            "filters": {
                "tag_type": "all",
                "tag_count_band": "11-14",
                "category": "operations",
                "component_name": "all",
                "page_name": "all",
            },
            "sort_order": "tag_desc",
            "grouping_mode": "tag_type",
            "search_query": "",
        },
        {
            "id": "customer_view",
            "name": "Customer View",
            "quick_switch": True,
            "filters": {
                "tag_type": "all",
                "tag_count_band": "all",
                "category": "customer",
                "component_name": "all",
                "page_name": "all",
            },
            "sort_order": "title_asc",
            "grouping_mode": "none",
            "search_query": "",
        },
        {
            "id": "delivery_view",
            "name": "Delivery View",
            "quick_switch": True,
            "filters": {
                "tag_type": "all",
                "tag_count_band": "all",
                "category": "delivery",
                "component_name": "all",
                "page_name": "all",
            },
            "sort_order": "tag_desc",
            "grouping_mode": "none",
            "search_query": "",
        },
        {
            "id": "executive_view",
            "name": "Executive View",
            "quick_switch": True,
            "filters": {
                "tag_type": "all",
                "tag_count_band": "15+",
                "category": "all",
                "component_name": "all",
                "page_name": "all",
            },
            "sort_order": "tag_desc",
            "grouping_mode": "category",
            "search_query": "",
        },
    ]


@dataclass
class SlideBlueprint:
    slide_id: str
    source_file: str
    title: str
    component_name: str
    page_name: str
    route: str
    category: str
    has_explicit_category: bool
    labels: list
    has_explicit_labels: bool
    tags: list

    @property
    def preview_components(self):
        previews = []
        for tag in self.tags:
            if tag.get("tag") != "ComponentPreview":
                continue
            attrs = tag.get("attrs", {})
            component_name = attrs.get("component") or attrs.get("name") or attrs.get("id")
            if component_name:
                previews.append(component_name)
        return previews


class PresentationContractError(RuntimeError):
    def __init__(self, errors):
        self.errors = list(errors)
        message = "Presentation contract validation failed:\n" + "\n".join(f"- {err}" for err in self.errors)
        super().__init__(message)


def _slugify(value):
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return clean or "slide"


def _pascal_case(value):
    parts = re.split(r"[^a-zA-Z0-9]+", value)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def _extract_title(text, fallback):
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _extract_tags(text):
    tags = []
    for match in TAG_PATTERN.finditer(text):
        tag_name = match.group("tag")
        if tag_name not in SUPPORTED_BLUEPRINT_TAGS:
            continue
        attrs = {key: value for key, value in ATTR_PATTERN.findall(match.group("attrs") or "")}
        tags.append({"tag": tag_name, "attrs": attrs})
    return tags


def _parse_frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text

    end_index = text.find("\n---\n", 4)
    if end_index == -1:
        return {}, text

    frontmatter_block = text[4:end_index]
    body = text[end_index + 5 :]
    metadata = {}
    for line in frontmatter_block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, body


def _parse_slide(path):
    text = path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(text)

    slide_id = _slugify(path.stem)
    title = frontmatter.get("title") or _extract_title(body, path.stem.replace("_", " ").title())
    base_name = _pascal_case(path.stem)
    component_name = f"{base_name}SlideGenerated"
    page_name = f"{base_name}PageGenerated"
    route = f"/homepage/slides/{slide_id}"
    raw_category = (frontmatter.get("category") or "").strip()
    raw_labels = (frontmatter.get("labels") or "").strip()
    category = _slugify(raw_category or "general")
    labels = [_slugify(label) for label in raw_labels.split(",") if label.strip()]

    return SlideBlueprint(
        slide_id=slide_id,
        source_file=path.name,
        title=title,
        component_name=component_name,
        page_name=page_name,
        route=route,
        category=category,
        has_explicit_category=bool(raw_category),
        labels=labels,
        has_explicit_labels=bool(raw_labels),
        tags=_extract_tags(body),
    )


def _validate_slide_contract(blueprints):
    errors = []
    warnings = []

    index_by_attr = {
        "slide_id": defaultdict(list),
        "route": defaultdict(list),
        "component_name": defaultdict(list),
        "page_name": defaultdict(list),
    }

    for blueprint in blueprints:
        index_by_attr["slide_id"][blueprint.slide_id].append(blueprint.source_file)
        index_by_attr["route"][blueprint.route].append(blueprint.source_file)
        index_by_attr["component_name"][blueprint.component_name].append(blueprint.source_file)
        index_by_attr["page_name"][blueprint.page_name].append(blueprint.source_file)

        if not blueprint.has_explicit_category:
            errors.append(
                f"{blueprint.source_file}: missing required frontmatter category (for example: category: customer)."
            )
        elif blueprint.category not in ALLOWED_SLIDE_CATEGORIES:
            errors.append(
                f"{blueprint.source_file}: category '{blueprint.category}' is not allowed. "
                f"Allowed categories: {', '.join(sorted(ALLOWED_SLIDE_CATEGORIES))}."
            )

        if not blueprint.has_explicit_labels or not blueprint.labels:
            errors.append(f"{blueprint.source_file}: missing required frontmatter labels (for example: labels: health, revenue).")

        if not blueprint.tags:
            errors.append(f"{blueprint.source_file}: no supported blueprint tags found ({', '.join(sorted(SUPPORTED_BLUEPRINT_TAGS))}).")

        required_tags = GENERATION_RULES_BY_CATEGORY.get(blueprint.category, set())
        present_tags = {tag.get("tag") for tag in blueprint.tags if tag.get("tag")}
        missing_required_tags = sorted(required_tags - present_tags)
        if missing_required_tags:
            warnings.append(
                f"{blueprint.source_file}: category '{blueprint.category}' is missing recommended generation tags: "
                f"{', '.join(missing_required_tags)}."
            )

    for attr_name, values in index_by_attr.items():
        for value, source_files in values.items():
            if len(source_files) > 1:
                errors.append(
                    f"duplicate {attr_name} '{value}' found in slides: {', '.join(sorted(source_files))}."
                )

    return errors, warnings


def _matches_preset(slide, preset_filters):
    tag_type = preset_filters.get("tag_type", "all")
    tag_count_band = preset_filters.get("tag_count_band", "all")
    category = preset_filters.get("category", "all")
    component_name = preset_filters.get("component_name", "all")
    page_name = preset_filters.get("page_name", "all")

    if tag_type != "all" and tag_type not in slide.get("tags_by_type", {}):
        return False

    tag_count = int(slide.get("tag_count", 0))
    if tag_count_band == "0-10" and not (0 <= tag_count <= 10):
        return False
    if tag_count_band == "11-14" and not (11 <= tag_count <= 14):
        return False
    if tag_count_band == "15+" and not (tag_count >= 15):
        return False

    if category != "all" and slide.get("category") != category:
        return False
    if component_name != "all" and slide.get("component_name") != component_name:
        return False
    if page_name != "all" and slide.get("page_name") != page_name:
        return False

    return True


def _validate_preset_contract(manifest):
    errors = []
    warnings = []

    presets = manifest.get("summary", {}).get("presets", [])
    slides = manifest.get("slides", [])

    categories = {slide.get("category") for slide in slides if slide.get("category")}
    tag_types = set()
    component_names = {slide.get("component_name") for slide in slides if slide.get("component_name")}
    page_names = {slide.get("page_name") for slide in slides if slide.get("page_name")}
    for slide in slides:
        tag_types.update((slide.get("tags_by_type") or {}).keys())

    seen_ids = set()
    for preset in presets:
        preset_id = preset.get("id")
        if not preset_id:
            errors.append("preset contract: found preset without id.")
            continue
        if preset_id in seen_ids:
            errors.append(f"preset contract: duplicate preset id '{preset_id}'.")
        seen_ids.add(preset_id)

        if not preset.get("name"):
            errors.append(f"preset contract: preset '{preset_id}' is missing name.")

        filters = preset.get("filters") or {}
        required_filter_keys = {"tag_type", "tag_count_band", "category", "component_name", "page_name"}
        missing_filter_keys = sorted(required_filter_keys - set(filters.keys()))
        if missing_filter_keys:
            errors.append(f"preset contract: preset '{preset_id}' missing filters: {', '.join(missing_filter_keys)}.")
            continue

        if filters.get("tag_count_band") not in PRESET_ALLOWED_TAG_COUNT_BANDS:
            errors.append(
                f"preset contract: preset '{preset_id}' has invalid tag_count_band '{filters.get('tag_count_band')}'."
            )
        if filters.get("tag_type") != "all" and filters.get("tag_type") not in tag_types:
            errors.append(f"preset contract: preset '{preset_id}' references unknown tag_type '{filters.get('tag_type')}'.")
        if filters.get("category") != "all" and filters.get("category") not in categories:
            errors.append(f"preset contract: preset '{preset_id}' references unknown category '{filters.get('category')}'.")
        if filters.get("component_name") != "all" and filters.get("component_name") not in component_names:
            errors.append(
                f"preset contract: preset '{preset_id}' references unknown component_name '{filters.get('component_name')}'."
            )
        if filters.get("page_name") != "all" and filters.get("page_name") not in page_names:
            errors.append(f"preset contract: preset '{preset_id}' references unknown page_name '{filters.get('page_name')}'.")

        if preset.get("sort_order") not in PRESET_ALLOWED_SORT_ORDERS:
            errors.append(f"preset contract: preset '{preset_id}' has invalid sort_order '{preset.get('sort_order')}'.")
        if preset.get("grouping_mode") not in PRESET_ALLOWED_GROUPING_MODES:
            errors.append(
                f"preset contract: preset '{preset_id}' has invalid grouping_mode '{preset.get('grouping_mode')}'."
            )

        matching_slides = [slide for slide in slides if _matches_preset(slide, filters)]
        if not matching_slides:
            warnings.append(f"preset stability: preset '{preset_id}' currently matches 0 slides.")

        sort_order = preset.get("sort_order")
        if sort_order in SORT_KEYS_WITHOUT_EXPLICIT_TIEBREAK and matching_slides:
            if sort_order in {"tag_desc", "tag_asc"}:
                value_counts = Counter(slide.get("tag_count", 0) for slide in matching_slides)
            else:
                value_counts = Counter((slide.get("title") or "") for slide in matching_slides)
            tied_values = [value for value, count in value_counts.items() if count > 1]
            if tied_values:
                warnings.append(
                    f"preset stability: preset '{preset_id}' uses sort '{sort_order}' with tied primary sort values; "
                    "results may appear unstable if input ordering changes."
                )

    return errors, warnings


def _validate_documentation_contract(base_dir):
    errors = []
    warnings = []

    readme_path = base_dir / "docs" / "architecture" / "presentation" / "README.md"
    checklist_path = base_dir / "docs" / "architecture" / "presentation" / "phase2_semantic_sprint_checklist.md"

    if not readme_path.exists():
        errors.append("documentation contract: missing README.md at docs/architecture/presentation/README.md.")
        return errors, warnings
    if not checklist_path.exists():
        errors.append(
            "documentation contract: missing checklist at docs/architecture/presentation/phase2_semantic_sprint_checklist.md."
        )
        return errors, warnings

    readme_text = readme_path.read_text(encoding="utf-8")
    checklist_text = checklist_path.read_text(encoding="utf-8")

    for marker in REQUIRED_README_MARKERS:
        if marker not in readme_text:
            errors.append(f"documentation contract: README.md missing marker '{marker}'.")

    for marker in REQUIRED_CHECKLIST_MARKERS:
        if marker not in checklist_text:
            errors.append(f"documentation contract: checklist missing marker '{marker}'.")

    if "Execution board" in readme_text and "phase2_semantic_sprint_checklist.md" not in readme_text:
        warnings.append(
            "documentation contract: README contains Execution board heading but no checklist path link was detected."
        )

    return errors, warnings


def _render_primitives():
    return """import React from \"react\";

export function LayoutGrid({ columns = \"2\", gap = \"16\", children }) {
  const numericColumns = Number(columns) || 2;
  const numericGap = Number(gap) || 16;
  return (
    <div
      style={{
        display: \"grid\",
        gridTemplateColumns: `repeat(${numericColumns}, minmax(0, 1fr))`,
        gap: `${numericGap}px`,
        marginBlock: \"1rem\",
      }}
    >
      {children}
    </div>
  );
}

export function Panel({ title = \"Panel\", tone = \"neutral\", children }) {
  const palette = {
    neutral: \"#e2e8f0\",
    primary: \"#bfdbfe\",
    success: \"#bbf7d0\",
    warning: \"#fde68a\",
    danger: \"#fecaca\",
  };

  return (
    <section
      style={{
        border: `1px solid ${palette[tone] || palette.neutral}`,
        borderRadius: \"12px\",
        padding: \"0.9rem\",
        background: \"#ffffff\",
      }}
    >
      <h4 style={{ marginTop: 0, marginBottom: \"0.45rem\" }}>{title}</h4>
      <div>{children}</div>
    </section>
  );
}

export function Quadrant({ label = \"Q\", emphasis = \"low\", children }) {
  const styleByEmphasis = {
    low: \"#e2e8f0\",
    medium: \"#bae6fd\",
    high: \"#fed7aa\",
    critical: \"#fca5a5\",
  };

  return (
    <article
      style={{
        border: `1px dashed ${styleByEmphasis[emphasis] || styleByEmphasis.low}`,
        borderRadius: \"10px\",
        padding: \"0.7rem\",
      }}
    >
      <strong style={{ display: \"block\", marginBottom: \"0.35rem\" }}>{label}</strong>
      <div>{children}</div>
    </article>
  );
}

export function ComponentPreview({ component = \"Unknown\", status = \"draft\" }) {
  return (
    <div
      style={{
        fontFamily: \"ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace\",
        fontSize: \"0.85rem\",
        border: \"1px solid #e2e8f0\",
        borderRadius: \"8px\",
        padding: \"0.45rem 0.6rem\",
        background: \"#f8fafc\",
      }}
    >
      preview: {component} ({status})
    </div>
  );
}
"""


def _render_slide_component(blueprint, mdx_import_path, primitive_import_path):
    return (
        "import React from \"react\";\n"
        f"import SlideDocument from \"{mdx_import_path}\";\n"
        f"import {{ LayoutGrid, Panel, Quadrant, ComponentPreview }} from \"{primitive_import_path}\";\n\n"
        "const mdxComponents = {\n"
        "  LayoutGrid,\n"
        "  Panel,\n"
        "  Quadrant,\n"
        "  ComponentPreview,\n"
        "};\n\n"
        f"export default function {blueprint.component_name}() {{\n"
        "  return <SlideDocument components={mdxComponents} />;\n"
        "}\n"
    )


def _render_page_component(blueprint):
    return (
        "import React from \"react\";\n"
        f"import {blueprint.component_name} from \"../{blueprint.component_name}\";\n\n"
        f"export default function {blueprint.page_name}() {{\n"
        "  return (\n"
        "    <section style={{ border: \"1px solid #e5e7eb\", borderRadius: \"14px\", padding: \"1rem\", marginTop: \"1rem\" }}>\n"
        f"      <h3 style={{{{ marginTop: 0 }}}}>{blueprint.title}</h3>\n"
        f"      <{blueprint.component_name} />\n"
        "    </section>\n"
        "  );\n"
        "}\n"
    )


def _render_registry_index(blueprints):
    import_lines = []
    component_entries = []
    page_entries = []
    registry_rows = []

    tag_totals = Counter()
    preview_totals = Counter()
    category_totals = Counter()
    presets = _default_registry_presets()

    for blueprint in blueprints:
        import_lines.append(f"import {blueprint.component_name} from \"./{blueprint.component_name}\";")
        import_lines.append(f"import {blueprint.page_name} from \"./pages/{blueprint.page_name}\";")
        component_entries.append(f'  "{blueprint.slide_id}": {blueprint.component_name},')
        page_entries.append(f'  "{blueprint.slide_id}": {blueprint.page_name},')

        tags_by_type = Counter(tag.get("tag", "") for tag in blueprint.tags if tag.get("tag"))
        tag_totals.update(tags_by_type)
        preview_totals.update(blueprint.preview_components)
        category_totals.update([blueprint.category])

        tags_by_type_parts = [f'"{key}": {value}' for key, value in sorted(tags_by_type.items())]
        tags_by_type_block = "{ " + ", ".join(tags_by_type_parts) + " }"
        preview_list = ", ".join(f'\"{name}\"' for name in blueprint.preview_components)
        labels_list = ", ".join(f'\"{name}\"' for name in blueprint.labels)

        registry_rows.append(
            "  {\n"
            f'    id: "{blueprint.slide_id}",\n'
            f'    title: "{blueprint.title}",\n'
            f'    route: "{blueprint.route}",\n'
            f'    category: "{blueprint.category}",\n'
            f'    labels: [{labels_list}],\n'
            f'    sourceFile: "{blueprint.source_file}",\n'
            f'    previewComponents: [{preview_list}],\n'
            f'    tagCount: {len(blueprint.tags)},\n'
            f'    tagsByType: {tags_by_type_block},\n'
            f'    componentName: "{blueprint.component_name}",\n'
            f'    pageName: "{blueprint.page_name}",\n'
            "  },"
        )

    imports_block = "\n".join(import_lines)
    rows_block = "\n".join(registry_rows)
    components_block = "\n".join(component_entries)
    pages_block = "\n".join(page_entries)
    tag_totals_block = "{ " + ", ".join(
        f'"{key}": {value}' for key, value in sorted(tag_totals.items())
    ) + " }"
    preview_totals_block = "{ " + ", ".join(
        f'"{key}": {value}' for key, value in sorted(preview_totals.items())
    ) + " }"
    category_totals_block = "{ " + ", ".join(
        f'"{key}": {value}' for key, value in sorted(category_totals.items())
    ) + " }"
    presets_block = json.dumps(presets, indent=2)

    return (
        f"{imports_block}\n\n"
        "export const generatedSlideRegistry = [\n"
        f"{rows_block}\n"
        "];\n\n"
        "export const generatedSlideRegistryMeta = {\n"
        f"  slideCount: {len(blueprints)},\n"
        f"  tagCount: {sum(len(blueprint.tags) for blueprint in blueprints)},\n"
        f"  previewComponentCount: {sum(preview_totals.values())},\n"
        f"  previewComponents: {preview_totals_block},\n"
        f"  tagTotals: {tag_totals_block},\n"
        f"  categoryTotals: {category_totals_block},\n"
        f"  presets: {presets_block},\n"
        "};\n\n"
        f"export const generatedSlidePresets = {presets_block};\n\n"
        "export const generatedSlideComponents = {\n"
        f"{components_block}\n"
        "};\n\n"
        "export const generatedSlidePages = {\n"
        f"{pages_block}\n"
        "};\n"
    )


def _validate_metadata_contract(blueprints):
    errors = []
    warnings = []

    for blueprint in blueprints:
        if blueprint.category not in ALLOWED_SLIDE_CATEGORIES:
            errors.append(
                f"[{blueprint.source_file}] invalid category '{blueprint.category}'. "
                f"Allowed categories: {', '.join(sorted(ALLOWED_SLIDE_CATEGORIES))}."
            )

        if not blueprint.labels:
            errors.append(f"[{blueprint.source_file}] requires at least one label in frontmatter.")

        if len(set(blueprint.labels)) != len(blueprint.labels):
            warnings.append(f"[{blueprint.source_file}] has duplicate labels; duplicates should be removed.")

        if len(blueprint.labels) > 8:
            warnings.append(f"[{blueprint.source_file}] has {len(blueprint.labels)} labels; keep labels focused.")

        if not blueprint.tags:
            errors.append(f"[{blueprint.source_file}] has no supported blueprint tags.")

    return errors, warnings


def _validate_generation_rules(blueprints):
    errors = []
    warnings = []

    for blueprint in blueprints:
        rule = GENERATION_RULES_BY_CATEGORY.get(blueprint.category)
        if not rule:
            warnings.append(
                f"[{blueprint.source_file}] has no generation rule profile for category '{blueprint.category}'."
            )
            continue

        tag_types = {tag.get("tag") for tag in blueprint.tags if tag.get("tag")}
        missing = sorted(rule - tag_types)
        if missing:
            errors.append(
                f"[{blueprint.source_file}] violates generation rules for category '{blueprint.category}'. "
                f"Missing required tags: {', '.join(missing)}."
            )

    return errors, warnings


def _apply_preset_to_slides(slides, preset):
    filters = preset.get("filters", {})
    tag_type = filters.get("tag_type", "all")
    tag_count_band = filters.get("tag_count_band", "all")
    category = filters.get("category", "all")
    component_name = filters.get("component_name", "all")
    page_name = filters.get("page_name", "all")
    needle = (preset.get("search_query") or "").strip().lower()
    sort_order = preset.get("sort_order", "title_asc")

    def _tag_count_match(value):
        if tag_count_band == "all":
            return True
        if tag_count_band == "0-10":
            return 0 <= value <= 10
        if tag_count_band == "11-14":
            return 11 <= value <= 14
        if tag_count_band == "15+":
            return value >= 15
        return False

    filtered = []
    for slide in slides:
        tags_by_type = slide.get("tags_by_type", {})
        if tag_type != "all" and tag_type not in tags_by_type:
            continue
        if not _tag_count_match(int(slide.get("tag_count") or 0)):
            continue
        if category != "all" and slide.get("category") != category:
            continue
        if component_name != "all" and slide.get("component_name") != component_name:
            continue
        if page_name != "all" and slide.get("page_name") != page_name:
            continue

        if needle:
            haystack = " ".join(
                [
                    slide.get("title") or "",
                    slide.get("source_file") or "",
                    slide.get("route") or "",
                    slide.get("component_name") or "",
                    slide.get("page_name") or "",
                    " ".join(slide.get("preview_components", [])),
                ]
            ).lower()
            if needle not in haystack:
                continue

        filtered.append(slide)

    if sort_order == "tag_desc":
        filtered.sort(key=lambda row: (-int(row.get("tag_count") or 0), row.get("title") or "", row.get("id") or ""))
    elif sort_order == "tag_asc":
        filtered.sort(key=lambda row: (int(row.get("tag_count") or 0), row.get("title") or "", row.get("id") or ""))
    elif sort_order == "title_desc":
        filtered.sort(key=lambda row: (row.get("title") or "", row.get("id") or ""), reverse=True)
    elif sort_order == "category_asc":
        filtered.sort(key=lambda row: (row.get("category") or "", row.get("title") or "", row.get("id") or ""))
    else:
        filtered.sort(key=lambda row: (row.get("title") or "", row.get("id") or ""))

    return [row.get("id") for row in filtered]


def _validate_preset_contract(slides, presets):
    errors = []
    warnings = []

    category_names = {slide.get("category") for slide in slides}
    component_names = {slide.get("component_name") for slide in slides}
    page_names = {slide.get("page_name") for slide in slides}

    seen_ids = set()
    for preset in presets:
        preset_id = preset.get("id") or ""
        preset_name = preset.get("name") or ""
        filters = preset.get("filters")

        if not preset_id:
            errors.append("Preset contract violation: missing preset id.")
            continue

        if preset_id in seen_ids:
            errors.append(f"Preset contract violation: duplicate preset id '{preset_id}'.")
        seen_ids.add(preset_id)

        if not preset_name:
            errors.append(f"Preset contract violation: '{preset_id}' is missing a name.")

        if not isinstance(filters, dict):
            errors.append(f"Preset contract violation: '{preset_id}' is missing filters object.")
            continue

        for required_key in ["tag_type", "tag_count_band", "category", "component_name", "page_name"]:
            if required_key not in filters:
                errors.append(f"Preset contract violation: '{preset_id}' missing filters.{required_key}.")

        sort_order = preset.get("sort_order")
        if sort_order not in PRESET_ALLOWED_SORT_ORDERS:
            errors.append(
                f"Preset contract violation: '{preset_id}' has unsupported sort_order '{sort_order}'."
            )

        grouping_mode = preset.get("grouping_mode")
        if grouping_mode not in PRESET_ALLOWED_GROUPING_MODES:
            errors.append(
                f"Preset contract violation: '{preset_id}' has unsupported grouping_mode '{grouping_mode}'."
            )

        category_value = filters.get("category", "all")
        if category_value != "all" and category_value not in category_names:
            errors.append(
                f"Preset '{preset_id}' references unknown category '{category_value}'."
            )

        component_value = filters.get("component_name", "all")
        if component_value != "all" and component_value not in component_names:
            errors.append(
                f"Preset '{preset_id}' references unknown component_name '{component_value}'."
            )

        page_value = filters.get("page_name", "all")
        if page_value != "all" and page_value not in page_names:
            errors.append(
                f"Preset '{preset_id}' references unknown page_name '{page_value}'."
            )

        resolved_once = _apply_preset_to_slides(slides, preset)
        resolved_twice = _apply_preset_to_slides(slides, preset)
        if resolved_once != resolved_twice:
            errors.append(
                f"Preset '{preset_id}' produced unstable slide ordering across repeated resolution."
            )

        if not resolved_once:
            warnings.append(f"Preset '{preset_id}' resolves to zero slides for current registry.")

        if resolved_once and sort_order in {"tag_desc", "tag_asc", "title_desc"}:
            matched_rows = [row for row in slides if row.get("id") in set(resolved_once)]
            if sort_order in {"tag_desc", "tag_asc"}:
                value_counts = Counter(int(row.get("tag_count") or 0) for row in matched_rows)
            else:
                value_counts = Counter((row.get("title") or "") for row in matched_rows)

            if any(count > 1 for count in value_counts.values()):
                warnings.append(
                    f"Preset '{preset_id}' may produce unstable ordering due to tied primary sort values for '{sort_order}'."
                )

    return errors, warnings


def _validate_documentation_sync(base_dir, presets):
    errors = []
    warnings = []

    readme_path = base_dir / "docs" / "architecture" / "presentation" / "README.md"
    checklist_path = base_dir / "docs" / "architecture" / "presentation" / "phase2_semantic_sprint_checklist.md"

    if not readme_path.exists():
        errors.append(f"Documentation sync error: missing required file {readme_path}.")
        return errors, warnings
    if not checklist_path.exists():
        errors.append(f"Documentation sync error: missing required file {checklist_path}.")
        return errors, warnings

    readme_text = readme_path.read_text(encoding="utf-8")
    checklist_text = checklist_path.read_text(encoding="utf-8")

    required_readme_fragments = [
        "summary.presets",
        "generatedSlidePresets",
        "generatedSlideRegistryMeta.presets",
        "phase2_semantic_sprint_checklist.md",
    ]
    for fragment in required_readme_fragments:
        if fragment not in readme_text:
            errors.append(f"README governance mismatch: missing '{fragment}'.")

    for preset in presets:
        if preset.get("name") and preset["name"] not in readme_text:
            warnings.append(
                f"README governance warning: preset name '{preset['name']}' not listed in saved preset section."
            )

    required_checklist_fragments = [
        "Day 6 - Integrate Semantic Layer",
        "Day 8 - Add Semantic Coverage Linter",
        "Day 9 - Browser Regression and Scripted Validation",
    ]
    for fragment in required_checklist_fragments:
        if fragment not in checklist_text:
            errors.append(f"Checklist governance mismatch: missing '{fragment}'.")

    return errors, warnings


def sync_presentation_blueprints(base_dir):
    if not isinstance(base_dir, Path):
        base_dir = Path(base_dir)

    architecture_presentation = base_dir / "docs" / "architecture" / "presentation"
    slides_dir = architecture_presentation / "slides"
    architecture_generated_dir = architecture_presentation / "ui" / "generated"

    frontend_generated_dir = base_dir / "frontend_homepage" / "src" / "ui" / "generated"
    frontend_generated_pages_dir = frontend_generated_dir / "pages"
    frontend_slides_dir = base_dir / "frontend_homepage" / "src" / "presentation" / "slides"

    slides_dir.mkdir(parents=True, exist_ok=True)
    architecture_generated_dir.mkdir(parents=True, exist_ok=True)
    frontend_generated_dir.mkdir(parents=True, exist_ok=True)
    frontend_generated_pages_dir.mkdir(parents=True, exist_ok=True)
    frontend_slides_dir.mkdir(parents=True, exist_ok=True)

    slide_paths = sorted(slides_dir.glob("*.mdx"))
    blueprints = [_parse_slide(path) for path in slide_paths]
    presets = _default_registry_presets()

    validation_errors = []
    validation_warnings = []

    metadata_errors, metadata_warnings = _validate_metadata_contract(blueprints)
    generation_errors, generation_warnings = _validate_generation_rules(blueprints)
    validation_errors.extend(metadata_errors)
    validation_errors.extend(generation_errors)
    validation_warnings.extend(metadata_warnings)
    validation_warnings.extend(generation_warnings)

    validation_slides = []
    for blueprint in blueprints:
        slide_tags_by_type = Counter(tag.get("tag", "") for tag in blueprint.tags if tag.get("tag"))
        validation_slides.append(
            {
                "id": blueprint.slide_id,
                "title": blueprint.title,
                "route": blueprint.route,
                "category": blueprint.category,
                "source_file": blueprint.source_file,
                "preview_components": blueprint.preview_components,
                "tag_count": len(blueprint.tags),
                "tags_by_type": dict(sorted(slide_tags_by_type.items())),
                "component_name": blueprint.component_name,
                "page_name": blueprint.page_name,
            }
        )

    preset_errors, preset_warnings = _validate_preset_contract(validation_slides, presets)
    docs_errors, docs_warnings = _validate_documentation_sync(base_dir, presets)
    validation_errors.extend(preset_errors)
    validation_errors.extend(docs_errors)
    validation_warnings.extend(preset_warnings)
    validation_warnings.extend(docs_warnings)

    if validation_errors:
        raise ValueError("\n".join(["Presentation contract validation failed:"] + validation_errors))

    for existing in frontend_slides_dir.glob("*.mdx"):
        existing.unlink()
    for path in slide_paths:
        shutil.copyfile(path, frontend_slides_dir / path.name)

    primitives_source = _render_primitives()
    (architecture_generated_dir / "primitives.jsx").write_text(primitives_source, encoding="utf-8")
    (frontend_generated_dir / "primitives.jsx").write_text(primitives_source, encoding="utf-8")

    for existing in architecture_generated_dir.glob("*.generated.jsx"):
        existing.unlink()
    for existing in architecture_generated_dir.glob("*SlideGenerated.jsx"):
        existing.unlink()
    for existing in frontend_generated_dir.glob("*.generated.jsx"):
        existing.unlink()
    for existing in frontend_generated_dir.glob("*SlideGenerated.jsx"):
        existing.unlink()
    for existing in frontend_generated_pages_dir.glob("*.generated.jsx"):
        existing.unlink()
    for existing in frontend_generated_pages_dir.glob("*PageGenerated.jsx"):
        existing.unlink()

    overall_tag_totals = Counter()
    overall_preview_components = Counter()
    overall_categories = Counter()

    manifest = {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "slides": [],
        "summary": {
            "slide_count": 0,
            "tag_count": 0,
            "tags_by_type": {},
            "preview_components": {},
            "categories": {},
            "presets": _default_registry_presets(),
        },
    }

    for blueprint in blueprints:
        architecture_component_source = _render_slide_component(
            blueprint,
            mdx_import_path=f"../../slides/{blueprint.source_file}",
            primitive_import_path="./primitives",
        )
        frontend_component_source = _render_slide_component(
            blueprint,
            mdx_import_path=f"../../presentation/slides/{blueprint.source_file}",
            primitive_import_path="./primitives",
        )

        (architecture_generated_dir / f"{blueprint.component_name}.jsx").write_text(
            architecture_component_source,
            encoding="utf-8",
        )
        (frontend_generated_dir / f"{blueprint.component_name}.jsx").write_text(
            frontend_component_source,
            encoding="utf-8",
        )

        page_source = _render_page_component(blueprint)
        (frontend_generated_pages_dir / f"{blueprint.page_name}.jsx").write_text(
            page_source,
            encoding="utf-8",
        )

        slide_tags_by_type = Counter(tag.get("tag", "") for tag in blueprint.tags if tag.get("tag"))
        manifest["slides"].append(
            {
                "id": blueprint.slide_id,
                "title": blueprint.title,
                "route": blueprint.route,
                "category": blueprint.category,
                "labels": blueprint.labels,
                "source_file": blueprint.source_file,
                "preview_components": blueprint.preview_components,
                "tags": blueprint.tags,
                "tag_count": len(blueprint.tags),
                "tags_by_type": dict(sorted(slide_tags_by_type.items())),
                "component_name": blueprint.component_name,
                "page_name": blueprint.page_name,
            }
        )

        overall_tag_totals.update(slide_tags_by_type)
        overall_preview_components.update(blueprint.preview_components)
        overall_categories.update([blueprint.category])

    manifest["summary"] = {
        "slide_count": len(blueprints),
        "tag_count": sum(len(blueprint.tags) for blueprint in blueprints),
        "tags_by_type": dict(sorted(overall_tag_totals.items())),
        "preview_components": dict(sorted(overall_preview_components.items())),
        "categories": dict(sorted(overall_categories.items())),
        "presets": presets,
    }

    registry_index_source = _render_registry_index(blueprints)
    (frontend_generated_dir / "index.js").write_text(registry_index_source, encoding="utf-8")

    registry_json = json.dumps(manifest, indent=2)
    (architecture_generated_dir / "manifest.json").write_text(registry_json, encoding="utf-8")
    (frontend_generated_dir / "registry.json").write_text(registry_json, encoding="utf-8")

    return {
        "slides_dir": str(slides_dir),
        "generated_dir": str(architecture_generated_dir),
        "frontend_generated_dir": str(frontend_generated_dir),
        "slide_count": len(blueprints),
        "tag_count": sum(len(blueprint.tags) for blueprint in blueprints),
        "validation_warnings": validation_warnings,
    }
