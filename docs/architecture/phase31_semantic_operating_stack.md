# Phase 31 Semantic Operating Stack

This phase extends deterministic RR -> RGB identity into five coordinated tracks.

## Engine-Truth Rule

All RR visual, workflow, and publishing surfaces derive color from persisted `Business.display_rgb`, `Business.compartment_id`, and `Business.color_code` (or deterministic fallback from canonical compartment metadata).

## Track 1: RR Visual System

API surfaces:
- `GET /seeds/api/rr/dashboard/`
- `GET /seeds/api/rr/industry-map/`
- `GET /seeds/api/rr/card-spec/`

Contract highlights:
- Dashboard lanes are keyed by `compartment_id` and fixed at 16 subjects.
- Status bands expose Idea/Seed/Project/Archived counts.
- Integrity strip exposes `ok`, `mismatch`, and `unavailable` counts.
- Industry map rows align to sector phases and expose RR density + mismatch overlays.

## Track 2: Middle Layer Integration

`get_project_middle_layer_activation_payload()` now includes `rr_color_context`, exposing:
- `lane_count`
- `status_bands`
- `integrity_strip`
- `dominant_lanes`

`/project-middle-layer/dashboard/` renders RR color context blocks with lane tinting from anchor bands.

## Track 3: VA Guidance Mode

API surface:
- `GET /seeds/api/rr/va-guidance/`

Guidance output includes:
- dominant compartments
- sector distribution
- integrity mismatch hotspots
- deterministic recommendations for SOP balancing and phase mix

## Track 4 and 5: Operational + Publishing Contracts

API surface:
- `GET /seeds/api/rr/operating-stack/`

Canonical catalog:
- `platform_semantic/catalogs/semantic_operating_stack.json`

Catalog defines:
- modular SOP unit schema
- workflow macro/micro/provenance schema
- investor e-book section structure
- product usage e-book section structure
- SOP -> workflow -> usage -> insight -> chapter assembly pipeline

## Verification

Run focused tests:

```bash
python manage.py test seeds.tests project_middle_layer.tests
```
