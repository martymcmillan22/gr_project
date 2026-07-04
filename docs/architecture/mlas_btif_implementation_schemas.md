# MLAS + BTIF Implementation Schemas

## Purpose
Translate the canonical MLAS/BTIF semantics into implementation-ready contracts for:
- Django models
- DRF serializers and API payloads
- UI routing resolver
- Preset registry

This document is designed to be coded directly with minimal interpretation.

## Canonical Routing Order
Use this exact resolver order in backend and frontend:

phase -> mlas -> color -> dewey -> industry -> metaphor -> category -> layout_archetype -> component_pack

Resolver rule: color is derived from phase + MLAS context.

## Django Model Blueprint

```python
from django.db import models


class Slide(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    # Core semantic inputs
    phase = models.CharField(max_length=16, choices=[
        ("create", "Create"),
        ("post", "Post"),
        ("work", "Work"),
    ])
    color_primary = models.CharField(max_length=24)
    metaphor = models.CharField(max_length=32, choices=[
        ("immune_system", "Immune System"),
        ("mycelium", "Mycelium"),
        ("botanist", "Botanist"),
    ])

    # MLAS
    mlas_subject = models.CharField(max_length=32)
    mlas_branch = models.CharField(max_length=32)
    mlas_term = models.CharField(max_length=32, blank=True)
    mlas_meta = models.CharField(max_length=32, blank=True)

    # Dewey
    dewey_code = models.CharField(max_length=16)

    # Industry taxonomy
    industry_super_sector = models.CharField(max_length=64)
    industry_sector = models.CharField(max_length=64)
    industry_group = models.CharField(max_length=64)
    industry_sub_industry = models.CharField(max_length=64)

    # Optional explicit category override
    ui_category_override = models.CharField(max_length=32, blank=True)

    # Derived routing outputs (cached)
    phase_resolved = models.CharField(max_length=16, blank=True)
    nav_group = models.CharField(max_length=32, blank=True)
    page_signature = models.CharField(max_length=32, blank=True)
    layout_archetype = models.CharField(max_length=32, blank=True)
    component_pack = models.CharField(max_length=32, blank=True)
    ui_category_resolved = models.CharField(max_length=32, blank=True)

    preset_key = models.CharField(max_length=128, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## Preset Registry Model

```python
class SemanticPreset(models.Model):
  # Canonical preset name format: phase.color.domain
  name = models.CharField(max_length=128, unique=True)
    key = models.CharField(max_length=128, unique=True)
    phase = models.CharField(max_length=16)
    color_primary = models.CharField(max_length=24)

    mlas_subject = models.CharField(max_length=32)
    mlas_branch = models.CharField(max_length=32)
    mlas_term = models.CharField(max_length=32, blank=True)
    mlas_meta = models.CharField(max_length=32, blank=True)

    dewey_code = models.CharField(max_length=16)
    metaphor = models.CharField(max_length=32)
    ui_category = models.CharField(max_length=32)

    industry_super_sector = models.CharField(max_length=64, blank=True)
    industry_sector = models.CharField(max_length=64)
    industry_group = models.CharField(max_length=64, blank=True)
    industry_sub_industry = models.CharField(max_length=64, blank=True)

    layout_archetype = models.CharField(max_length=32)
    component_pack = models.CharField(max_length=32)
    page_signature = models.CharField(max_length=32)
    nav_group = models.CharField(max_length=32)
```

## DRF API Contracts

### Slide Create/Update payload

```json
{
  "title": "Quantitative Spores",
  "slug": "quantitative-spores",
  "phase": "post",
  "color_primary": "purple",
  "metaphor": "mycelium",
  "mlas_subject": "math",
  "mlas_branch": "sacp",
  "mlas_term": "cnic",
  "mlas_meta": "ddnc",
  "dewey_code": "500",
  "industry_super_sector": "financials",
  "industry_sector": "banking",
  "industry_group": "financial-analytics",
  "industry_sub_industry": "quant-finance",
  "ui_category_override": "customer",
  "preset_key": "post.purple.statistics"
}
```

### Slide response payload (resolved)

```json
{
  "id": 42,
  "title": "Quantitative Spores",
  "phase": "post",
  "phase_resolved": "post",
  "color_primary": "purple",
  "metaphor": "mycelium",
  "mlas": {
    "subject": "math",
    "branch": "sacp",
    "term": "cnic",
    "meta": "ddnc"
  },
  "dewey": {
    "code": "500",
    "nav_group": "information"
  },
  "industry": {
    "super_sector": "financials",
    "sector": "banking",
    "group": "financial-analytics",
    "sub_industry": "quant-finance",
    "page_signature": "analytical"
  },
  "ui": {
    "category": "customer",
    "layout_archetype": "journey",
    "component_pack": "narrative-pack",
    "behavior_profile": "mycelium"
  },
  "preset_key": "post.purple.statistics"
}
```

## Preset Naming Convention
- `SemanticPreset.name` must be formatted as `phase.color.domain`.
- Canonical examples:
  - `create.red.math`
  - `create.blue.language`
  - `post.purple.statistics`
  - `post.teal.literature`
  - `work.pink.history`
  - `work.cyan.geography`

## Deterministic Routing Tables

### 1) Phase -> default category and metaphor
| phase | metaphor | ui_category |
| --- | --- | --- |
| create | immune_system | operations |
| post | mycelium | customer |
| work | botanist | delivery |

If work + executive context is present, ui_category may resolve to executive.

### 2) Color -> layout
| color | layout_archetype |
| --- | --- |
| red | matrix |
| blue | matrix |
| yellow | matrix |
| green | matrix |
| purple | journey |
| teal | journey |
| orange | journey |
| lime | journey |
| pink | pipeline |
| cyan | pipeline |
| amber | pipeline |
| green-lime | pipeline |

### 3) MLAS depth -> component pack
| signal | component_pack |
| --- | --- |
| subject-only | foundational-pack |
| branch set | narrative-pack |
| term set | structural-pack |
| meta set | deep-pack |

Resolution rule:
- If meta exists -> deep-pack
- Else if term exists -> structural-pack
- Else if branch exists -> narrative-pack
- Else -> foundational-pack

### 4) Dewey -> navigation
| dewey range | nav_group |
| --- | --- |
| 100-400 | foundations |
| 500-800 | information |
| 900-1000 | systems |

### 5) Industry -> page signature
| industry family | page_signature |
| --- | --- |
| financials | analytical |
| communications | narrative |
| consumer | experiential |
| industrials | operational |

## Resolver Pseudocode

```python
def resolve_ui(slide):
    phase_defaults = {
        "create": {"metaphor": "immune_system", "category": "operations"},
        "post": {"metaphor": "mycelium", "category": "customer"},
        "work": {"metaphor": "botanist", "category": "delivery"},
    }

    phase_resolved = slide.phase
    default = phase_defaults[phase_resolved]
    metaphor = slide.metaphor or default["metaphor"]
    ui_category = slide.ui_category_override or default["category"]

    layout = color_to_layout(slide.color_primary)
    nav_group = dewey_to_nav(slide.dewey_code)
    page_signature = industry_to_signature(slide.industry_super_sector, slide.industry_sector)
    component_pack = mlas_depth_to_component_pack(
        slide.mlas_subject,
        slide.mlas_branch,
        slide.mlas_term,
        slide.mlas_meta,
    )

    return {
      "phase_resolved": phase_resolved,
        "metaphor": metaphor,
        "ui_category": ui_category,
        "layout_archetype": layout,
        "nav_group": nav_group,
        "page_signature": page_signature,
        "component_pack": component_pack,
    }
```

## Preset Apply Contract
Applying preset must be atomic and idempotent.

Algorithm:
1. Lookup preset by key.
2. Fill all unset semantic fields.
3. Recompute resolved routing fields.
4. Persist with one transaction.

Expected API:
- POST /api/slides/{id}/apply-preset/
- Body: {"preset_key": "post.purple.statistics"}

Response returns full resolved slide payload.

## Validation Constraints
- phase, color_primary, mlas_subject, mlas_branch, dewey_code required.
- metaphor must match phase family unless override flag is enabled.
- dewey_code must map to a known nav group.
- color_primary must map to exactly one layout archetype.
- mlas depth cannot skip level (meta requires term and branch context).
- if `phase=work` and `ui_category_override` is empty, resolver must set `ui_category_resolved=delivery`.
- if `component_pack=deep-pack`, then `mlas_meta` must be present.
