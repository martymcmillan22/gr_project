"""
QPU pre-routing service for PIP - the "green tier engine".

Phase 3 scope only: prepare payloads for the existing workflow/ Strict Mode
QPU engine, and gate invocation at DCHD tier. This does NOT modify the Strict
Mode engine itself, and does NOT yet wire in SRL/ConvectionCycle/temporal
context into the engine's internals - the engine remains stateless with no
concept of user/tier/SRL/Convection (confirmed during Phase 3 investigation).

Phase 4 will add: temporal routing, SRL->QPU mapping, Convection->QPU mapping,
and the Enterprise lifecycle state.
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
        """Gate on DCHD tier, then execute the existing StrictModeEngine unmodified."""
        from workflow.engine.strict_mode_engine import StrictModeEngine  # deferred: keep workflow/ decoupled

        if not QPUService.can_invoke(pip_state):
            raise QPUAccessDeniedError(
                f"QPU requires DCHD tier; current tier is {pip_state.final_tier}."
            )

        definition = json.loads(STRICT_MODE_DEFINITION_PATH.read_text(encoding="utf-8"))
        engine = StrictModeEngine(definition)
        return engine.run(payload)
