from project_middle_layer.schemas import ProjectSchema


def build_semantic_tree_mermaid(schema: ProjectSchema) -> str:
    tags = "\n".join(
        [f"    PM[{schema['slug']}] --> TAG_{tag.replace('-', '_')}[tag:{tag}]" for tag in schema["semantic_tags"]]
    )
    return "\n".join(
        [
            "graph TD",
            f"    PM[{schema['slug']}] --> INTENT[{schema['semantic_intent']}]",
            f"    PM[{schema['slug']}] --> MLAS[{schema['mlas_tier']}]",
            f"    PM[{schema['slug']}] --> BTIF[{schema['btif_classification']}]",
            tags,
        ]
    )
