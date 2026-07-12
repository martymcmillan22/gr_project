from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


try:
    from workflow.schema.genre_classifier_schema import (
        GENRE_CLASSIFIER_SCHEMA,
        validate_genre_classifier_output,
    )
except ModuleNotFoundError:  # pragma: no cover - script execution path
    GENRE_CLASSIFIER_SCHEMA = {
        "schema_id": "genre-classifier-output",
        "schema_version": "1.0.0",
        "workflow_id": "genre-classifier",
        "required": ["genre", "confidence", "signals_used", "semantic_summary"],
    }

    def validate_genre_classifier_output(payload):
        required = GENRE_CLASSIFIER_SCHEMA["required"]
        missing = [key for key in required if key not in payload]
        if missing:
            return False, f"Missing required keys: {missing}"
        if not isinstance(payload.get("genre"), str) or not payload["genre"].strip():
            return False, "genre must be a non-empty string"
        confidence = payload.get("confidence")
        if not isinstance(confidence, (int, float)):
            return False, "confidence must be numeric"
        if confidence < 0 or confidence > 1:
            return False, "confidence must be between 0 and 1"
        if not isinstance(payload.get("signals_used"), list):
            return False, "signals_used must be a list"
        if not isinstance(payload.get("semantic_summary"), str) or not payload["semantic_summary"].strip():
            return False, "semantic_summary must be a non-empty string"
        return True, "ok"


try:
    from workflow.metadata.genre_classifier_metadata import GENRE_CLASSIFIER_METADATA
except ModuleNotFoundError:  # pragma: no cover - script execution path
    GENRE_CLASSIFIER_METADATA = {
        "id": "genre-classifier",
        "name": "Genre Classifier Workflow",
        "semantic_tags": [
            "genre",
            "classification",
            "semantic",
            "storytelling-engine",
            "strict-mode",
            "creator-workflow",
        ],
        "btif_subjects": ["Math", "Language", "Arts", "Science"],
        "classification": {
            "type": "workflow",
            "tier": "genre-classifier",
            "category": "semantic-classification",
            "engine": "BTPE",
        },
        "genre_taxonomy": [
            "Action",
            "Drama",
            "Comedy",
            "Thriller",
            "Romance",
            "Sci-Fi",
            "Fantasy",
            "Mystery",
            "Horror",
        ],
    }


try:
    from workflow.propagation.genre_classifier_propagation import GenreClassifierPropagation
except ModuleNotFoundError:  # pragma: no cover - script execution path

    class GenreClassifierPropagation:
        def __init__(self):
            self.metadata = GENRE_CLASSIFIER_METADATA

        def attach_metadata(self, qpu_output):
            return {
                "workflow_id": self.metadata["id"],
                "workflow_name": self.metadata["name"],
                "semantic_tags": self.metadata["semantic_tags"],
                "btif_subjects": self.metadata["btif_subjects"],
                "classification": self.metadata["classification"],
                "genre_taxonomy": self.metadata["genre_taxonomy"],
                "qpu_output": qpu_output,
            }

        def propagate(self, qpu_output):
            enriched = self.attach_metadata(qpu_output)
            return {
                "genre_enriched": enriched,
                "btpe_layer": {
                    "intent": "Genre-Classification",
                    "tags": enriched["semantic_tags"],
                    "subjects": enriched["btif_subjects"],
                    "workflow": enriched["workflow_id"],
                    "classification": enriched["classification"],
                    "genre_taxonomy": enriched["genre_taxonomy"],
                },
            }


CANONICAL_RELAY_ORDER = [
    "red",
    "blue",
    "yellow",
    "green",
    "purple",
    "teal",
    "orange",
    "lime",
    "pink",
    "cyan",
    "amber",
    "green-lime",
]

TENSE_ORDER = {
    "past": 1,
    "present-past": 2,
    "present_future": 3,
    "present-future": 3,
    "future": 4,
}

GENRE_ORDER = [
    "Action",
    "Drama",
    "Comedy",
    "Thriller",
    "Romance",
    "Sci-Fi",
    "Fantasy",
    "Mystery",
    "Horror",
]


@dataclass
class SignalBundle:
    inverse_pair_tension: float
    relay_geometry: float
    srl_scaling_curve: float
    temporal_bias: float
    semantic_density: float
    semantic_tags: list[str]
    subjects: list[str]
    tenses: list[str]
    signals_used: list[str]
    signal_labels: dict[str, str]


class SignalExtractionNode:
    def __init__(self, config):
        self.config = config

    def _normalize_inverse_pairs(self, inverse_pairs):
        normalized = []
        for pair in inverse_pairs:
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                normalized.append((str(pair[0]).strip().lower(), str(pair[1]).strip().lower()))
        return normalized

    def _relay_geometry_score(self, relay_segment):
        if len(relay_segment) != 4:
            return 0.0, "incomplete"

        positions = []
        for color in relay_segment:
            if color in CANONICAL_RELAY_ORDER:
                positions.append(CANONICAL_RELAY_ORDER.index(color))
            else:
                return 0.15, "divergent"

        deltas = [positions[i + 1] - positions[i] for i in range(len(positions) - 1)]
        if deltas == [1, 1, 1]:
            return 1.0, "linear"
        if all(delta > 0 for delta in deltas):
            if max(deltas) > 1:
                return 0.45, "divergent"
            return 0.8, "progressive"
        if deltas == [2, 2, 2] or deltas == [-2, -2, -2]:
            return 0.65, "oscillating"
        return 0.25, "divergent"

    def _temporal_bias_score(self, tenses):
        ordered = [TENSE_ORDER.get(str(tense).strip().lower(), 0) for tense in tenses if str(tense).strip()]
        if not ordered:
            return 0.0, "unknown"

        first = ordered[0]
        last = ordered[-1]
        average = sum(ordered) / len(ordered)
        trend = last - first

        if trend >= 2:
            return min(1.0, 0.5 + (trend / 4)), "forward"
        if trend <= -2:
            return min(1.0, 0.5 + (abs(trend) / 4)), "past-dominant"
        if average >= 2.5:
            return 0.78, "present-future"
        if average <= 1.75:
            return 0.76, "past-dominant"
        return 0.6, "balanced"

    def _srl_curve_score(self, srl_values):
        values = [int(value) for value in srl_values if isinstance(value, (int, float))]
        if len(values) != 4:
            return 0.0, "invalid"

        ratios = []
        for left, right in zip(values, values[1:]):
            if left == 0:
                ratios.append(0.0)
            else:
                ratios.append(right / left)

        if ratios == [4.0, 4.0, 4.0]:
            return 1.0, "acceleration"
        if all(ratio >= 1.5 for ratio in ratios) and ratios[0] <= ratios[-1]:
            return 0.82, "acceleration"
        if all(ratio <= 1.0 for ratio in ratios):
            return 0.86, "compression"
        if ratios[0] > ratios[-1]:
            return 0.68, "breadcrumbing"
        return 0.5, "mixed"

    def _semantic_density_score(self, semantic_tags):
        tags = [str(tag).strip().lower() for tag in semantic_tags if str(tag).strip()]
        density = len(set(tags)) / max(len(tags), 1)
        return min(1.0, density), tags

    def run(self, qpu):
        if not isinstance(qpu, dict):
            raise ValueError("Genre Classifier expects a Strict Mode QPU dictionary.")

        inverse_pairs = self._normalize_inverse_pairs(qpu.get("inverse_pairs", []))
        relay_segment = [str(color).strip().lower() for color in qpu.get("relay_segment", []) if str(color).strip()]
        srl_values = [int(value) for value in qpu.get("srl_values", []) if isinstance(value, (int, float, str))]
        temporal_rows = qpu.get("qpu", [])
        semantic = qpu.get("semantic", {}) if isinstance(qpu.get("semantic", {}), dict) else {}

        tenses = []
        subjects = []
        for row in temporal_rows:
            if isinstance(row, dict):
                tense = str(row.get("tense", "")).strip().lower()
                subject = str(row.get("subject", "")).strip()
                if tense:
                    tenses.append(tense)
                if subject:
                    subjects.append(subject)

        semantic_tags_input = semantic.get("tags", qpu.get("semantic_tags", []))
        semantic_density, semantic_tags = self._semantic_density_score(semantic_tags_input)
        temporal_score, temporal_profile = self._temporal_bias_score(tenses)
        srl_score, srl_profile = self._srl_curve_score(srl_values)
        relay_score, relay_profile = self._relay_geometry_score(relay_segment)

        inverse_pair_tension = 0.0
        if len(inverse_pairs) == 2:
            unique_colors = {color for pair in inverse_pairs for color in pair}
            if len(unique_colors) == 4:
                inverse_pair_tension = 0.0
            else:
                inverse_pair_tension = 0.55
        elif inverse_pairs:
            inverse_pair_tension = 0.35
        else:
            inverse_pair_tension = 0.1

        signal_labels = {
            "inverse_pair_tension": "corruption" if inverse_pair_tension >= 0.5 else "harmony",
            "relay_geometry": relay_profile,
            "srl_scaling_curve": srl_profile,
            "temporal_bias": temporal_profile,
            "semantic_density": "expansive" if semantic_density >= 0.75 else "compact",
        }

        signals_used = [
            "inverse pair tension",
            "relay geometry",
            "SRL scaling curve",
            "temporal bias",
            "semantic tags",
        ]

        return SignalBundle(
            inverse_pair_tension=inverse_pair_tension,
            relay_geometry=relay_score,
            srl_scaling_curve=srl_score,
            temporal_bias=temporal_score,
            semantic_density=semantic_density,
            semantic_tags=semantic_tags,
            subjects=subjects,
            tenses=tenses,
            signals_used=signals_used,
            signal_labels=signal_labels,
        )


class GenreRuleEngineNode:
    def __init__(self, config):
        self.genres = config.get("genres", GENRE_ORDER)

    def _has_tags(self, tags, needles):
        tag_set = {str(tag).strip().lower() for tag in tags}
        return any(needle in tag_set for needle in needles)

    def _rule_scores(self, signals: SignalBundle):
        inverse_harmony = max(0.0, 1.0 - signals.inverse_pair_tension)
        tension = signals.inverse_pair_tension
        linearity = signals.relay_geometry
        acceleration = signals.srl_scaling_curve
        temporal = signals.temporal_bias
        density = signals.semantic_density
        tags = signals.semantic_tags

        past_bias = 1.0 if any(tense == "past" for tense in signals.tenses[:2]) else 0.0
        future_bias = 1.0 if any(tense == "future" for tense in signals.tenses[-2:]) else 0.0
        present_future_bias = 1.0 if "present-future" in signals.tenses else 0.0
        past_dominant = 1.0 if signals.signal_labels["temporal_bias"] == "past-dominant" else 0.0
        forward_bias = 1.0 if signals.signal_labels["temporal_bias"] == "forward" else 0.0
        future_tension = 1.0 if signals.signal_labels["temporal_bias"] in {"forward", "present-future"} else 0.0
        compression = 1.0 if signals.signal_labels["srl_scaling_curve"] == "compression" else 0.0
        acceleration_profile = 1.0 if signals.signal_labels["srl_scaling_curve"] == "acceleration" else 0.0
        breadcrumbing = 1.0 if signals.signal_labels["srl_scaling_curve"] == "breadcrumbing" else 0.0
        divergence = 1.0 if signals.signal_labels["relay_geometry"] == "divergent" else 0.0
        oscillation = 1.0 if signals.signal_labels["relay_geometry"] == "oscillating" else 0.0
        mythic_tags = 1.0 if self._has_tags(tags, {"fantasy", "myth", "mythic", "legend"}) else 0.0
        conceptual_tags = 1.0 if self._has_tags(tags, {"conceptual", "concept", "semantic", "expansion"}) else 0.0
        decay_tags = 1.0 if self._has_tags(tags, {"decay", "corruption", "horror", "dark"}) else 0.0
        playfulness = 1.0 if self._has_tags(tags, {"comedy", "playful", "humor", "satire"}) else 0.0

        return {
            "Action": round((0.35 * acceleration_profile) + (0.25 * forward_bias) + (0.2 * acceleration) + (0.2 * linearity), 3),
            "Drama": round((0.45 * tension) + (0.2 * past_bias) + (0.15 * (1.0 - density)) + (0.2 * (1.0 - playfulness)), 3),
            "Comedy": round((0.35 * oscillation) + (0.25 * playfulness) + (0.2 * (1.0 - tension)) + (0.2 * (1.0 - compression)), 3),
            "Thriller": round((0.35 * compression) + (0.25 * future_tension) + (0.2 * tension) + (0.2 * linearity), 3),
            "Romance": round((0.35 * inverse_harmony) + (0.25 * present_future_bias) + (0.2 * linearity) + (0.2 * (1.0 - tension)), 3),
            "Sci-Fi": round((0.4 * conceptual_tags) + (0.25 * future_bias) + (0.2 * density) + (0.15 * acceleration), 3),
            "Fantasy": round((0.35 * divergence) + (0.25 * mythic_tags) + (0.2 * density) + (0.2 * (1.0 - tension)), 3),
            "Mystery": round((0.35 * breadcrumbing) + (0.25 * past_dominant) + (0.2 * linearity) + (0.2 * tension), 3),
            "Horror": round((0.4 * decay_tags) + (0.25 * tension) + (0.2 * (1.0 - inverse_harmony)) + (0.15 * (1.0 - density)), 3),
        }

    def run(self, signals: SignalBundle):
        scores = self._rule_scores(signals)
        ordered = sorted(scores.items(), key=lambda item: (-item[1], self.genres.index(item[0]) if item[0] in self.genres else 999))
        genre, score = ordered[0]
        runner_up = ordered[1][1] if len(ordered) > 1 else 0.0
        confidence = max(0.5, min(0.99, round(0.58 + (score * 0.32) + ((score - runner_up) * 0.18), 2)))

        return {
            "genre": genre,
            "confidence": confidence,
            "signals_used": signals.signals_used,
            "semantic_summary": self._semantic_summary(genre, signals),
            "genre_scores": scores,
        }

    def _semantic_summary(self, genre, signals: SignalBundle):
        temporal = signals.signal_labels["temporal_bias"]
        relay = signals.signal_labels["relay_geometry"]
        srl = signals.signal_labels["srl_scaling_curve"]
        if genre == "Action":
            return f"High acceleration and {temporal} momentum with {relay} relay geometry."
        if genre == "Drama":
            return f"Structural tension is concentrated in inverse pairing and emotional conflict."
        if genre == "Comedy":
            return f"Oscillating relay geometry and playful inversion create a light semantic profile."
        if genre == "Thriller":
            return f"Compressed SRL motion and {temporal} tension create a suspenseful structural profile."
        if genre == "Romance":
            return f"Inverse harmony and {temporal} progression support a relational arc."
        if genre == "Sci-Fi":
            return f"Semantic density and conceptual expansion point to speculative structure."
        if genre == "Fantasy":
            return f"Relay divergence and mythic framing produce an expansive imaginative profile."
        if genre == "Mystery":
            return f"Breadcrumb SRL motion and past-dominant mapping support investigative tension."
        if genre == "Horror":
            return f"Corruption, decay, and structural tension create a destabilized semantic layer."
        return f"Balanced structural signals with {srl} SRL behavior and {temporal} temporal motion."


class ClassificationOutputNode:
    def __init__(self, config):
        self.config = config

    def run(self, genre_result):
        genre = genre_result["genre"]
        confidence = genre_result["confidence"]
        signals_used = genre_result["signals_used"]
        semantic_summary = genre_result["semantic_summary"]

        return {
            "genre": genre,
            "confidence": confidence,
            "signals_used": signals_used,
            "semantic_summary": semantic_summary,
        }


class GenreClassifierEngine:
    """
    Executes the Genre Classifier workflow as defined in genre_classifier.workflow.json.
    This module provides deterministic node sequencing and structural genre classification.
    """

    def __init__(self, definition):
        self.definition = definition
        self.nodes = self._load_nodes(definition)
        self.propagation = GenreClassifierPropagation()

    def _load_nodes(self, definition):
        node_map = {}

        for node_def in definition["nodes"]:
            node_id = node_def["id"]
            config = node_def.get("config", {})

            if node_id == "signal_extraction_node":
                node_map[node_id] = SignalExtractionNode(config)
            elif node_id == "genre_rule_engine_node":
                node_map[node_id] = GenreRuleEngineNode(config)
            elif node_id == "classification_output_node":
                node_map[node_id] = ClassificationOutputNode(config)

        return node_map

    def run(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("Genre Classifier expects a Strict Mode QPU dictionary.")

        source_id = payload.get("workflow_id", "strict-mode")
        seed_name = payload.get("name", "Strict Mode QPU")

        signals = self.nodes["signal_extraction_node"].run(payload)
        genre_result = self.nodes["genre_rule_engine_node"].run(signals)
        classification = self.nodes["classification_output_node"].run(genre_result)

        propagated = self.propagation.propagate(classification)

        output = {
            **classification,
            "source_workflow_id": source_id,
            "source_name": seed_name,
        }

        is_valid, reason = validate_genre_classifier_output(output)
        if not is_valid:
            raise ValueError(f"[GENRE_CLASSIFIER_SCHEMA_INVALID] {reason}")

        return {
            **output,
            "genre_enriched": propagated.get("genre_enriched"),
            "btpe_layer": propagated.get("btpe_layer"),
            "schema": {
                "schema_id": GENRE_CLASSIFIER_SCHEMA.get("schema_id"),
                "schema_version": GENRE_CLASSIFIER_SCHEMA.get("schema_version"),
                "valid": True,
            },
            "semantic": {
                "intent": "Genre-Classification",
                "tags": GENRE_CLASSIFIER_METADATA.get("semantic_tags", []),
                "btif_subjects": GENRE_CLASSIFIER_METADATA.get("btif_subjects", []),
                "classification": GENRE_CLASSIFIER_METADATA.get("classification", {}),
                "genre_taxonomy": GENRE_CLASSIFIER_METADATA.get("genre_taxonomy", GENRE_ORDER),
            },
        }
