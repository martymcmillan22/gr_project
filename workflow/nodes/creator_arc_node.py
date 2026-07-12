try:
    from workflow.errors.creator_workflow_errors import CreatorBeatCountError
except ModuleNotFoundError:  # pragma: no cover - script execution path
    from errors.creator_workflow_errors import CreatorBeatCountError


class CreatorArcNode:
    def __init__(self, config):
        self.beat_titles = config.get("beat_titles", ["Setup", "Development", "Pivot", "Resolution"])

    def run(self, seed_context):
        source_qpu = seed_context["source_qpu"]
        if len(source_qpu) != 4:
            raise CreatorBeatCountError(len(source_qpu))

        story_beats = []
        for index, item in enumerate(source_qpu):
            beat_title = self.beat_titles[index] if index < len(self.beat_titles) else f"Beat {index + 1}"
            story_beats.append(
                {
                    "beat": index + 1,
                    "title": beat_title,
                    "tense": item.get("tense", ""),
                    "srl": item.get("srl"),
                    "subject": item.get("subject", ""),
                    "summary": (
                        f"{beat_title} anchors the narrative in {item.get('subject', 'the source material')} "
                        f"through {item.get('tense', 'the mapped tense')} at SRL {item.get('srl')}"
                    ),
                }
            )

        return {**seed_context, "story_beats": story_beats}
