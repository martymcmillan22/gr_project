PHASE_CREATE = "create"
PHASE_POST = "post"
PHASE_WORK = "work"

BTIF_PHASE_ORDER = (PHASE_CREATE, PHASE_POST, PHASE_WORK)
BTIF_COMPARTMENTS_BY_PHASE = {
    PHASE_CREATE: ("R", "B", "Y", "G"),
    PHASE_POST: ("P", "T", "O", "L"),
    PHASE_WORK: ("P", "C", "A", "G-L"),
}

ASSIGNMENT_LINEAR = "linear"
ASSIGNMENT_DOUBLE_LINEAR = "double_linear"
ASSIGNMENT_TWELVE_POINT = "twelve_point"
ASSIGNMENT_PERPETUAL = "perpetual"

ASSIGNMENT_CHOICES = (
    (ASSIGNMENT_LINEAR, "Linear Assignment"),
    (ASSIGNMENT_DOUBLE_LINEAR, "2x Linear Assignment"),
    (ASSIGNMENT_TWELVE_POINT, "12-Point Assignment"),
    (ASSIGNMENT_PERPETUAL, "Perpetual Assignment"),
)

ASSIGNMENT_DOCUMENT_TITLES = {
    ASSIGNMENT_LINEAR: "Linear document",
    ASSIGNMENT_DOUBLE_LINEAR: "2xlinear document",
    ASSIGNMENT_TWELVE_POINT: "12 Point Document",
    ASSIGNMENT_PERPETUAL: "Perpetual Document",
}

ITEM_STATUS_RECEIVED = "received"
ITEM_STATUS_WORKING = "working"
ITEM_STATUS_COMPLETED = "completed"

ITEM_STATUS_CHOICES = (
    (ITEM_STATUS_RECEIVED, "Received"),
    (ITEM_STATUS_WORKING, "Working"),
    (ITEM_STATUS_COMPLETED, "Completed"),
)


TASK_ARCHETYPE_DEFINITIONS = {
    ASSIGNMENT_LINEAR: {
        "key": ASSIGNMENT_LINEAR,
        "label": "Linear Assignment",
        "document_title": "Linear document",
        "governance_class": "deterministic_compartment_structure",
        "compartment_count": 4,
        "tracks": 1,
        "cycles": 1,
        "phase_scope": (PHASE_CREATE,),
        "compartment_slots": {
            "track_a": BTIF_COMPARTMENTS_BY_PHASE[PHASE_CREATE],
        },
        "canonical_compartments": {
            "track_a": (
                {"slot": "A1", "compartment": "R", "label": "Start / Intake"},
                {"slot": "A2", "compartment": "B", "label": "Development"},
                {"slot": "A3", "compartment": "Y", "label": "Refinement"},
                {"slot": "A4", "compartment": "G", "label": "Finalization / Output"},
            ),
        },
        "use_cases": (
            "monthly_newsletter_issue",
            "simple_editorial_tasks",
            "single_track_workflows",
            "lightweight_governance_loops",
        ),
        "governance": {
            "routing": "sequential",
            "drift_detection": "per_compartment",
            "va_narration": "per_step",
            "polish_refinement": "compartments_2_to_3",
        },
    },
    ASSIGNMENT_DOUBLE_LINEAR: {
        "key": ASSIGNMENT_DOUBLE_LINEAR,
        "label": "2x Linear Assignment",
        "document_title": "2x Linear document",
        "governance_class": "deterministic_compartment_structure",
        "compartment_count": 8,
        "tracks": 2,
        "cycles": 1,
        "phase_scope": (PHASE_CREATE, PHASE_POST),
        "compartment_slots": {
            "track_a": BTIF_COMPARTMENTS_BY_PHASE[PHASE_CREATE],
            "track_b": BTIF_COMPARTMENTS_BY_PHASE[PHASE_POST],
        },
        "canonical_compartments": {
            "track_a": (
                {"slot": "A1", "compartment": "R", "label": "Intake"},
                {"slot": "A2", "compartment": "B", "label": "Development"},
                {"slot": "A3", "compartment": "Y", "label": "Refinement"},
                {"slot": "A4", "compartment": "G", "label": "Output"},
            ),
            "track_b": (
                {"slot": "B1", "compartment": "P", "label": "Intake"},
                {"slot": "B2", "compartment": "T", "label": "Development"},
                {"slot": "B3", "compartment": "O", "label": "Refinement"},
                {"slot": "B4", "compartment": "L", "label": "Output"},
            ),
        },
        "use_cases": (
            "issue_plus_sidebar",
            "main_story_plus_audience_signals",
            "two_editorial_streams",
            "dual_deliverable_pipelines",
        ),
        "governance": {
            "routing": "parallel",
            "drift_detection": "cross_track",
            "va_narration": "track_comparison",
            "polish_refinement": "track_independent",
        },
    },
    ASSIGNMENT_TWELVE_POINT: {
        "key": ASSIGNMENT_TWELVE_POINT,
        "label": "12-Point Assignment",
        "document_title": "12 Point Document",
        "governance_class": "deterministic_compartment_structure",
        "compartment_count": 12,
        "tracks": 1,
        "cycles": 1,
        "phase_scope": BTIF_PHASE_ORDER,
        "compartment_slots": {
            "track_a": (
                *BTIF_COMPARTMENTS_BY_PHASE[PHASE_CREATE],
                *BTIF_COMPARTMENTS_BY_PHASE[PHASE_POST],
                *BTIF_COMPARTMENTS_BY_PHASE[PHASE_WORK],
            ),
        },
        "canonical_compartments": {
            "track_a": tuple(
                {
                    "slot": f"P{index + 1}",
                    "compartment": compartment,
                    "label": f"Narrative / analytical point {index + 1}",
                }
                for index, compartment in enumerate(
                    (
                        *BTIF_COMPARTMENTS_BY_PHASE[PHASE_CREATE],
                        *BTIF_COMPARTMENTS_BY_PHASE[PHASE_POST],
                        *BTIF_COMPARTMENTS_BY_PHASE[PHASE_WORK],
                    )
                )
            ),
        },
        "use_cases": (
            "annual_summary",
            "themed_issue",
            "deep_dive_editorial",
            "structured_analysis",
        ),
        "governance": {
            "routing": "structured_document",
            "drift_detection": "whole_document",
            "va_narration": "all_12_points",
            "polish_refinement": "document_wide",
        },
    },
    ASSIGNMENT_PERPETUAL: {
        "key": ASSIGNMENT_PERPETUAL,
        "label": "Perpetual Assignment",
        "document_title": "Perpetual Document",
        "governance_class": "deterministic_compartment_structure",
        "compartment_count": 24,
        "tracks": 2,
        "cycles": 2,
        "phase_scope": BTIF_PHASE_ORDER,
        "compartment_slots": {
            "track_a": (
                *BTIF_COMPARTMENTS_BY_PHASE[PHASE_CREATE],
                *BTIF_COMPARTMENTS_BY_PHASE[PHASE_POST],
                *BTIF_COMPARTMENTS_BY_PHASE[PHASE_WORK],
            ),
            "track_b": (
                *BTIF_COMPARTMENTS_BY_PHASE[PHASE_CREATE],
                *BTIF_COMPARTMENTS_BY_PHASE[PHASE_POST],
                *BTIF_COMPARTMENTS_BY_PHASE[PHASE_WORK],
            ),
        },
        "canonical_compartments": {
            "track_a": tuple(
                {
                    "slot": f"A{index + 1}",
                    "compartment": compartment,
                    "label": f"Editorial calendar lane {index + 1}",
                }
                for index, compartment in enumerate(
                    (
                        *BTIF_COMPARTMENTS_BY_PHASE[PHASE_CREATE],
                        *BTIF_COMPARTMENTS_BY_PHASE[PHASE_POST],
                        *BTIF_COMPARTMENTS_BY_PHASE[PHASE_WORK],
                    )
                )
            ),
            "track_b": tuple(
                {
                    "slot": f"B{index + 1}",
                    "compartment": compartment,
                    "label": f"Theme / signal lane {index + 1}",
                }
                for index, compartment in enumerate(
                    (
                        *BTIF_COMPARTMENTS_BY_PHASE[PHASE_CREATE],
                        *BTIF_COMPARTMENTS_BY_PHASE[PHASE_POST],
                        *BTIF_COMPARTMENTS_BY_PHASE[PHASE_WORK],
                    )
                )
            ),
        },
        "use_cases": (
            "annual_basetrue_newsletter_plan",
            "editorial_calendar",
            "theme_tracker",
            "rolling_narrative",
            "enterprise_24_hour_operations",
        ),
        "governance": {
            "routing": "continuous",
            "drift_detection": "cross_track_24_compartments",
            "va_narration": "dual_track_continuous",
            "polish_refinement": "evergreen",
            "quadrant_alignment": "deterministic_required",
        },
    },
}


def get_task_archetype_definition(assignment_type: str) -> dict:
    definition = TASK_ARCHETYPE_DEFINITIONS.get(assignment_type)
    if definition is None:
        raise ValueError(f"Unsupported assignment type: {assignment_type}")
    return definition


def list_task_archetype_definitions() -> list[dict]:
    return [TASK_ARCHETYPE_DEFINITIONS[key] for key, _ in ASSIGNMENT_CHOICES]

