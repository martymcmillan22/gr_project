from typing import NotRequired, TypedDict


class IdentityPayload(TypedDict):
    slug: str
    semantic_intent: str
    mlas_tier: str
    btif_classification: str
    name: NotRequired[str]
    semantic_tags: NotRequired[list[str]]
