class CreatorWorkflowError(Exception):
    """Base error for the Creator Workflow."""


class CreatorInputError(CreatorWorkflowError):
    def __init__(self, message):
        super().__init__(f"[CREATOR_INPUT] {message}")


class CreatorBeatCountError(CreatorWorkflowError):
    def __init__(self, count):
        super().__init__(f"[CREATOR_BEAT_COUNT] Expected 4 beats, received {count}.")


class CreatorOutlineCountError(CreatorWorkflowError):
    def __init__(self, count):
        super().__init__(f"[CREATOR_OUTLINE_COUNT] Expected 4 outline sections, received {count}.")


class CreatorNarrativeError(CreatorWorkflowError):
    def __init__(self, message):
        super().__init__(f"[CREATOR_NARRATIVE] {message}")
