# Presentation MDX Pipeline

This directory hosts slide-based UI blueprints that compile into React components and generated pages.

## Directory layout

- `slides/`: source MDX UI blueprints
- `ui/generated/`: generated React components + manifest from MDX parsing

## Standard MDX blueprint tags

Blueprint slides should use these tags so the scaffold parser can extract implementation intent:

- `LayoutGrid`: grid layout blocks (`columns`, `gap`)
- `Panel`: section wrapper blocks (`title`, `tone`)
- `Quadrant`: quadrant mapping blocks (`label`, `emphasis`)
- `ComponentPreview`: implementation target tags (`component`, `status`)

## Optional frontmatter for slide management

Use frontmatter to support scalable registry filters/grouping:

```md
---
category: customer
labels: health, revenue
---
```

- `category`: used for grouping and category filters.
- `labels`: comma-separated tags rendered as metadata chips.

## How generation works

1. Parse each `.mdx` file in `slides/`.
2. Extract supported tags and attributes.
3. Build manifest metadata (`ui/generated/manifest.json`).
4. Generate React components/pages into:
   - `docs/architecture/presentation/ui/generated/`
   - `frontend_homepage/src/ui/generated/`
5. Copy slide MDX files into `frontend_homepage/src/presentation/slides/` so Vite can compile them.

## Commands

Create a new slide blueprint and auto-sync generated React artifacts:

```bash
./a_gr_venv/bin/python manage.py create_presentation_slide <slide_name>
```

Example:

```bash
./a_gr_venv/bin/python manage.py create_presentation_slide customer_journey_canvas --title "Customer Journey Canvas"
```

Generate from MDX manually:

```bash
./a_gr_venv/bin/python manage.py sync_presentation_ui
```

The scaffold command now runs this automatically as part of standard workflow:

```bash
./a_gr_venv/bin/python manage.py scaffold_onepager <app_name>
```

## Registry management console features

The homepage registry panel supports:

- search across title/file/route/component/page/preview components
- filters by tag type, tag count, category, component name, and page name
- sorting by title, tag count, or category
- grouping by category or tag profile

### Saved filter presets

The registry loads built-in presets from generated metadata on page render:

- Operations View
- Customer View
- Delivery View
- Executive View

Each preset stores:

- selected filters (`tag_type`, `tag_count_band`, `category`, `component_name`, `page_name`)
- selected sort order
- selected grouping mode
- optional search query

Preset metadata is generated into:

- `docs/architecture/presentation/ui/generated/manifest.json` (`summary.presets`)
- `frontend_homepage/src/ui/generated/index.js` (`generatedSlidePresets` and `generatedSlideRegistryMeta.presets`)

Custom presets created in the UI are stored locally in browser storage and merged with built-in presets at runtime.

## Frontend and backend wiring

- Frontend uses MDX compilation via `@mdx-js/rollup` in Vite config.
- Generated slide metadata is exposed by Django/DRF at:
  - `/homepage/api/presentation-slides/`
- Homepage React app reads this endpoint and shows the slide registry panel.

## Execution board

Use the Phase 2 working board checklist to run semantic intelligence work day-by-day with stop/go gates:

- `docs/architecture/presentation/phase2_semantic_sprint_checklist.md`
