GENRE_CLASSIFIER_METADATA = {
    "id": "genre-classifier",
    "name": "Genre Classifier Workflow",
    "description": (
        "Semantic metadata for the Genre Classifier workflow. "
        "Defines classification tags, BTIF lineage, and semantic intent "
        "for deterministic genre identification."
    ),
    "semantic_tags": [
        "genre",
        "classification",
        "semantic",
        "qpu",
        "structure",
        "analysis",
    ],
    "btif_subjects": [
        "Language",
        "Arts",
        "Science",
        "Math",
    ],
    "semantic_intent": "Genre-Classification",
    "nodes": {
        "signal_extraction_node": {
            "role": "signal-extraction",
            "description": "Extracts structural signals from Strict Mode QPU.",
        },
        "genre_rule_engine_node": {
            "role": "genre-rule-engine",
            "description": "Applies deterministic genre rules to classify narrative.",
        },
        "classification_output_node": {
            "role": "classification-output",
            "description": "Builds final genre classification payload.",
        },
    },
    "classification": {
        "type": "workflow",
        "tier": "semantic",
        "category": "genre-classification",
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
