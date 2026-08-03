"""
QPU pre-routing service for PIP - the "green tier engine".

Phase 3 scope only: prepare payloads for the existing workflow/ Strict Mode
QPU engine, and gate invocation at DCHD tier. This does NOT modify the Strict
Mode engine itself, and does NOT yet wire in SRL/ConvectionCycle/temporal
context into the engine's internals - the engine remains stateless with no
concept of user/tier/SRL/Convection (confirmed during Phase 3 investigation).

Phase 4 will add: temporal routing, SRL->QPU mapping, Convection->QPU mapping,
and the Enterprise lifecycle state.

Phase 4 update: QPU now also requires a forward-looking Convection-Cycle slot
(present_future or future) in addition to DCHD tier. If the tier check fails,
`run()` still raises QPUAccessDeniedError (unchanged from Phase 3). If tier is
fine but the time slot isn't forward-looking, `run()` returns a structured
{"status": "temporally_gated", ...} result instead of invoking the engine.
"""

import json
from pathlib import Path

STRICT_MODE_DEFINITION_PATH = (
    Path(__file__).resolve().parent.parent / "workflow" / "definitions" / "strict_mode.workflow.json"
)


class QPUAccessDeniedError(Exception):
    """Raised when a QPU action is attempted below the required tier."""


class QPUService:
    """Prepares Strict Mode QPU payloads and gates invocation by tier."""

    @staticmethod
    def can_invoke(pip_state):
        """QPU unlocks only at DCHD tier (see pip_state.qpu_unlocked)."""
        return pip_state.qpu_unlocked

    @staticmethod
    def prepare_payload(relay_segment, srl_values, btif_subjects):
        """Build a Strict Mode QPU payload. No tier enforcement here - see `run()`."""
        return {
            "relay_segment": relay_segment,
            "srl_values": srl_values,
            "btif_subjects": btif_subjects,
        }

    @staticmethod
    def run(pip_state, payload):
        """Gate on DCHD tier (raises) and a forward-looking time slot (returns a
        structured result), then execute the existing StrictModeEngine unmodified.
        """
        from workflow.engine.strict_mode_engine import StrictModeEngine  # deferred: keep workflow/ decoupled

        if not QPUService.can_invoke(pip_state):
            raise QPUAccessDeniedError(
                f"QPU requires DCHD tier; current tier is {pip_state.final_tier}."
            )

        if not pip_state.qpu_allowed_now:
            return {
                "status": "temporally_gated",
                "reason": (
                    "QPU requires a present_future/future Convection slot; "
                    f"current time_frame={pip_state.time_slot_time_frame}."
                ),
            }

        definition = json.loads(STRICT_MODE_DEFINITION_PATH.read_text(encoding="utf-8"))
        engine = StrictModeEngine(definition)
        return engine.run(payload)
