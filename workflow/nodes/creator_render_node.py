try:
    from workflow.errors.creator_workflow_errors import CreatorNarrativeError
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from errors.creator_workflow_errors import CreatorNarrativeError


class CreatorRenderNode:
    def __init__(self, config):
        self.render_style = config.get("render_style", "concise")
        self.scene_labels = config.get("scene_labels", ["Scene 1", "Scene 2", "Scene 3", "Scene 4"])

    def run(self, outline_context):
        outline = outline_context["outline"]
        if len(outline) != 4:
            raise CreatorNarrativeError("outline must contain four sections")

        scenes = []
        narrative_parts = []
        for index, section in enumerate(outline):
            scene_title = self.scene_labels[index] if index < len(self.scene_labels) else f"Scene {index + 1}"
            scene_text = (
                f"{scene_title}: {section['heading']} focuses on {section['summary']} "
                f"This keeps the creator workflow deterministic and reusable."
            )
            scenes.append(
                {
                    "scene": index + 1,
                    "label": scene_title,
                    "heading": section["heading"],
                    "text": scene_text,
                }
            )
            narrative_parts.append(scene_text)

        narrative = "\n\n".join(narrative_parts)
        if not narrative.strip():
            raise CreatorNarrativeError("narrative output is empty")

        return {
            **outline_context,
            "scenes": scenes,
            "narrative": narrative,
            "render_style": self.render_style,
        }
