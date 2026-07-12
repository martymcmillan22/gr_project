try:
    from workflow.nodes.creator_arc_node import CreatorArcNode
    from workflow.nodes.creator_outline_node import CreatorOutlineNode
    from workflow.nodes.creator_render_node import CreatorRenderNode
    from workflow.nodes.creator_seed_node import CreatorSeedNode
    from workflow.semantic.creator_workflow_propagation import CreatorWorkflowPropagation
    from workflow.semantic.creator_workflow_qpu_schema import (
        CREATOR_WORKFLOW_QPU_SCHEMA,
        build_creator_workflow_semantic_block,
        validate_creator_workflow_qpu,
    )
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from nodes.creator_arc_node import CreatorArcNode
    from nodes.creator_outline_node import CreatorOutlineNode
    from nodes.creator_render_node import CreatorRenderNode
    from nodes.creator_seed_node import CreatorSeedNode
    from semantic.creator_workflow_propagation import CreatorWorkflowPropagation
    from semantic.creator_workflow_qpu_schema import (
        CREATOR_WORKFLOW_QPU_SCHEMA,
        build_creator_workflow_semantic_block,
        validate_creator_workflow_qpu,
    )


class CreatorWorkflowEngine:
    def __init__(self, definition):
        self.definition = definition
        self.nodes = self._load_nodes(definition)
        self.propagation = CreatorWorkflowPropagation()

    def _load_nodes(self, definition):
        node_map = {}
        for node_def in definition["nodes"]:
            node_id = node_def["id"]
            config = node_def.get("config", {})

            if node_id == "creator_seed_node":
                node_map[node_id] = CreatorSeedNode(config)
            elif node_id == "creator_arc_node":
                node_map[node_id] = CreatorArcNode(config)
            elif node_id == "creator_outline_node":
                node_map[node_id] = CreatorOutlineNode(config)
            elif node_id == "creator_render_node":
                node_map[node_id] = CreatorRenderNode(config)

        return node_map

    def run(self, payload):
        seed_context = self.nodes["creator_seed_node"].run(payload)
        arc_context = self.nodes["creator_arc_node"].run(seed_context)
        outline_context = self.nodes["creator_outline_node"].run(arc_context)
        rendered_context = self.nodes["creator_render_node"].run(outline_context)

        base_result = {
            "workflow_id": self.definition.get("id", "creator-workflow"),
            "name": self.definition.get("name", payload.get("name", "Narrative Creator Workflow")),
            "source_workflow_id": rendered_context["source_workflow_id"],
            "source_name": rendered_context["source_name"],
            "source_qpu": rendered_context["source_qpu"],
            "story_beats": rendered_context["story_beats"],
            "outline": rendered_context["outline"],
            "scenes": rendered_context["scenes"],
            "narrative": rendered_context["narrative"],
            "semantic_tags": rendered_context.get("semantic_tags", []),
        }

        node_roles = {
            node_id: details.get("role", "")
            for node_id, details in self.propagation.metadata.get("nodes", {}).items()
        }
        semantic_block = build_creator_workflow_semantic_block(
            semantic_intent=self.propagation.metadata.get("semantic_intent", "QPU-Creator-Output"),
            semantic_tags=base_result["semantic_tags"],
            btif_subjects=self.propagation.metadata.get("btif_subjects", []),
            classification=self.propagation.metadata.get("classification", {}),
            node_roles=node_roles,
        )

        schema_payload = {
            "workflow_id": base_result["workflow_id"],
            "name": base_result["name"],
            "source_workflow_id": base_result["source_workflow_id"],
            "source_name": base_result["source_name"],
            "source_qpu": base_result["source_qpu"],
            "story_beats": base_result["story_beats"],
            "outline": base_result["outline"],
            "scenes": base_result["scenes"],
            "narrative": base_result["narrative"],
            "semantic": semantic_block,
        }

        is_valid, reason = validate_creator_workflow_qpu(schema_payload)
        if not is_valid:
            raise ValueError(f"[CREATOR_SCHEMA_INVALID] {reason}")

        propagated = self.propagation.propagate(base_result["narrative"])

        return {
            **base_result,
            "semantic": semantic_block,
            "creator_enriched": propagated["creator_enriched"],
            "btpe_layer": propagated["btpe_layer"],
            "schema": {
                "schema_id": CREATOR_WORKFLOW_QPU_SCHEMA.get("schema_id"),
                "schema_version": CREATOR_WORKFLOW_QPU_SCHEMA.get("schema_version"),
                "valid": True,
            },
        }
