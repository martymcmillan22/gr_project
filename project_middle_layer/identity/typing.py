from typing import TypedDict


class IdentityPayload(TypedDict):
    slug: str
    semantic_intent: str
    mlas_tier: str
    btif_classification: str
