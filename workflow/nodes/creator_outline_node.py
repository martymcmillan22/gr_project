try:
    from workflow.errors.creator_workflow_errors import CreatorOutlineCountError
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from errors.creator_workflow_errors import CreatorOutlineCountError


class CreatorOutlineNode:
    def __init__(self, config):
        self.outline_sections = config.get("outline_sections", ["Premise", "Escalation", "Turning Point", "Closure"])

    def run(self, arc_context):
        story_beats = arc_context["story_beats"]
        if len(story_beats) != 4:
            raise CreatorOutlineCountError(len(story_beats))

        outline = []
        for index, beat in enumerate(story_beats):
            section = self.outline_sections[index] if index < len(self.outline_sections) else beat["title"]
            outline.append(
                {
                    "section": index + 1,
                    "heading": section,
                    "beat_title": beat["title"],
                    "summary": beat["summary"],
                    "purpose": f"Advance the {beat['title'].lower()} phase of the narrative.",
                }
            )

        return {**arc_context, "outline": outline}
