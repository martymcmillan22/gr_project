from project_middle_layer.schemas import ProjectSchema


def build_semantic_tree_mermaid(schema: ProjectSchema) -> str:
    tags = "\n".join(
        [f"    PROJECT --> TAG_{tag.replace('-', '_')}[tag:{tag}]" for tag in schema["semantic_tags"]]
    )

    return "\n".join(
        [
            "graph TD",
            "    IDEA[Idea] --> SEED[Seed]",
            f"    SEED --> PROJECT[{schema['slug']}]",
            "    PROJECT --> IDENTITY_BRANCH[Identity Branch]",
            "    IDENTITY_BRANCH --> SPECIALIZED_PATH[Specialized Path]",
            f"    PROJECT --> INTENT[{schema['semantic_intent']}]",
            f"    PROJECT --> MLAS[{schema['mlas_tier']}]",
            f"    PROJECT --> BTIF[{schema['btif_classification']}]",
            tags,
        ]
    )
