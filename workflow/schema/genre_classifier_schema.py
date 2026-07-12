GENRE_CLASSIFIER_SCHEMA = {
    "schema_id": "genre-classifier-output",
    "schema_version": "1.0.0",
    "workflow_id": "genre-classifier",
    "required": [
        "genre",
        "confidence",
        "signals_used",
        "semantic_summary",
    ],
    "properties": {
        "genre": {
            "type": "string",
            "allowed": [
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
        },
        "confidence": {
            "type": "number",
            "min": 0.0,
            "max": 1.0,
        },
        "signals_used": {
            "type": "array",
            "item_type": "string",
        },
        "semantic_summary": {
            "type": "string",
            "min_length": 1,
        },
    },
}


def validate(payload):
    required = GENRE_CLASSIFIER_SCHEMA["required"]
    missing = [key for key in required if key not in payload]
    if missing:
        return False

    genre = payload.get("genre")
    if not isinstance(genre, str) or not genre.strip():
        return False
    if genre not in GENRE_CLASSIFIER_SCHEMA["properties"]["genre"]["allowed"]:
        return False

    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)):
        return False
    if confidence < 0.0 or confidence > 1.0:
        return False

    signals_used = payload.get("signals_used")
    if not isinstance(signals_used, list):
        return False
    if any(not isinstance(signal, str) or not signal.strip() for signal in signals_used):
        return False

    semantic_summary = payload.get("semantic_summary")
    if not isinstance(semantic_summary, str) or not semantic_summary.strip():
        return False

    return True


def validate_genre_classifier_output(payload):
    is_valid = validate(payload)
    if is_valid:
        return True, "ok"
    return False, "genre classifier output failed schema validation"
