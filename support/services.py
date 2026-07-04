"""
Support clustering helpers.

All functions operate read-only on the Feedback and FAQ tables.
No ML — pure aggregation.
"""

from django.db.models import Count

from .models import FAQ, Feedback

# ---------------------------------------------------------------------------
# Auto-draft templates for quick FAQ creation.
# Each key matches a PATTERN_CHOICES value.  Values are (question, answer).
# These are starting points — the admin edits before publishing.
# ---------------------------------------------------------------------------
FAQ_DRAFT_TEMPLATES: dict[str, tuple[str, str]] = {
    "billing": (
        "Why was I charged an unexpected amount?",
        "We review all billing questions promptly. Common causes include plan upgrades, "
        "prorated charges, or renewal cycles. Please check your billing history in your "
        "account settings. If the charge still looks wrong, contact us directly.",
    ),
    "ui": (
        "I can't find [feature] — where is it?",
        "Navigation has recently been updated. [Describe where the feature now lives.] "
        "If you're still stuck, use the search bar at the top of the page or reach out "
        "to our support team.",
    ),
    "feature": (
        "Can [feature] be added to the platform?",
        "We actively track feature requests. This one has been noted and added to our "
        "roadmap review. We'll update this FAQ when the feature ships.",
    ),
    "bug": (
        "I encountered an error — what should I do?",
        "We're sorry you hit a problem. Try refreshing the page or clearing your browser "
        "cache first. If the issue persists, please report it using the feedback button "
        "and include what you were doing when it occurred.",
    ),
    "performance": (
        "The page is slow or not loading correctly — how do I fix this?",
        "Performance issues can be caused by network conditions or high load. Try "
        "refreshing, or come back in a few minutes. If slowness persists, please "
        "let us know via the feedback widget so we can investigate.",
    ),
    "other": (
        "I have a question that isn't covered here — how do I get help?",
        "Use the feedback button on this page or email support directly. We aim to "
        "respond within one business day.",
    ),
}


# ---------------------------------------------------------------------------
# Pattern classification keywords.
# Used by classify_feedback_pattern() to auto-tag feedback without human input.
# Keys are pattern tags; values are lists of keywords to match (case-insensitive).
# ---------------------------------------------------------------------------
PATTERN_KEYWORDS = {
    "billing": [
        "charge", "charged", "payment", "paid", "invoice", "receipt", "refund",
        "credit card", "subscription", "renewal", "plan", "upgrade", "downgrade",
        "pricing", "cost", "fee", "amount", "expensive", "discount", "coupon",
        "bill", "account balance", "transaction", "unexpected charge",
    ],
    "ui": [
        "button", "menu", "nav", "navigation", "find", "where", "locate", "click",
        "visible", "see", "hidden", "layout", "screen", "interface", "page",
        "sidebar", "toolbar", "icon", "link", "broken link", "dark mode", "theme",
        "scroll", "stuck", "loading", "spinning", "freeze", "hang",
    ],
    "feature": [
        "add", "feature", "request", "want", "need", "missing", "could you",
        "would be nice", "it would help", "suggestion", "roadmap", "planned",
        "export", "import", "api", "integration", "third-party", "plugin",
    ],
    "bug": [
        "error", "bug", "crash", "broken", "not working", "issue", "problem",
        "fail", "failed", "exception", "traceback", "stack trace", "404", "500",
        "timeout", "connection", "lost", "disconnect", "corrupted", "data loss",
    ],
    "performance": [
        "slow", "fast", "speed", "delay", "lag", "hang", "freeze", "timeout",
        "load", "loading", "unresponsive", "cpu", "memory", "resource",
        "optimize", "performance", "faster", "quicker", "instant",
    ],
}


def classify_feedback_pattern(text: str) -> str:
    """
    Auto-classify feedback text into a pattern tag using keyword heuristics.

    Algorithm:
    1. Lowercase the text
    2. For each pattern, count keyword matches
    3. Return the pattern with the highest score
    4. If no matches, return "" (unclassified)

    Returns one of: "billing", "ui", "feature", "bug", "performance", or ""
    """
    if not text or not text.strip():
        return ""

    text_lower = text.lower()
    scores = {}

    for pattern_tag, keywords in PATTERN_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in text_lower:
                score += 1
        scores[pattern_tag] = score

    # Find the highest-scoring pattern.
    best_pattern = max(scores, key=scores.get) if scores else ""
    best_score = scores.get(best_pattern, 0)

    # If no pattern scored > 0, return unclassified.
    if best_score == 0:
        return ""

    return best_pattern


def faq_draft_for_pattern(pattern_tag: str) -> tuple[str, str]:
    """
    Return a (question, answer) draft tuple for a given pattern_tag.
    Falls back to generic placeholders for unknown tags.
    """
    return FAQ_DRAFT_TEMPLATES.get(
        pattern_tag,
        (
            f"[Draft] Common question about {pattern_tag}",
            "[Draft answer — fill in before publishing.]",
        ),
    )


def _build_faq_map(top_n: int = 3) -> dict[str, list]:
    """
    Single-query lookup: returns {pattern_tag: [FAQ, ...]} for all active,
    tagged FAQs ordered by effectiveness_score.

    Each list is capped at top_n entries so callers get the most-relevant
    FAQs without extra slicing.
    """
    faq_map: dict[str, list] = {}
    qs = (
        FAQ.objects.filter(is_active=True)
        .exclude(pattern_tag="")
        .order_by("-priority", "order", "id")
    )
    # Fetch and sort by effectiveness score.
    faqs = list(qs)
    faqs.sort(key=lambda f: -faq_effectiveness_score(f))

    for faq in faqs:
        bucket = faq_map.setdefault(faq.pattern_tag, [])
        if len(bucket) < top_n:
            bucket.append(faq)
    return faq_map


def faq_effectiveness_score(faq) -> float:
    """
    Combine priority + effectiveness into a single score for ranking.

    Score = priority * 1000 + effectiveness_ratio * 100

    This ensures priority dominates, but within the same priority tier,
    we prefer FAQs with better positive/negative ratios.
    """
    # Avoid division by zero; treat zero hits as neutral (0.5 ratio).
    total = faq.positive_hits + faq.negative_hits
    if total == 0:
        effectiveness_ratio = 0.5
    else:
        effectiveness_ratio = faq.positive_hits / total

    return faq.priority * 1000 + effectiveness_ratio * 100


def ranked_suggested_faqs(pattern_tag: str, top_n: int = 3) -> list:
    """
    Return active FAQs linked to pattern_tag, ranked by effectiveness_score:

    Score = priority * 1000 + (positive_hits / total_hits) * 100

    This prioritizes by:
        1. Priority (CRITICAL > HIGH > ELEVATED > NORMAL)
        2. Effectiveness ratio (within same priority tier)
        3. Order & id as tiebreaker

    Returns at most top_n entries.  When all effectiveness is neutral (no hits),
    falls back to insertion order, providing a safe deterministic ordering.
    """
    qs = FAQ.objects.filter(is_active=True, pattern_tag=pattern_tag).order_by("-priority", "order", "id")
    faqs = list(qs)
    # Sort by effectiveness score (highest first), keeping determinism via order+id.
    faqs.sort(key=lambda f: -faq_effectiveness_score(f))
    return faqs[:top_n]


def negative_pattern_clusters(min_count: int = 1, top_n: int = 10) -> list[dict]:
    """
    Return a ranked list of negative feedback patterns, each enriched with
    the top suggested FAQs (by priority → order → id).

    Each entry is a dict:
        {
            "pattern_tag":        str,
            "label":              str,
            "count":              int,
            "is_high_importance": bool,
            "suggested_faqs":     list[FAQ],   # ordered, capped at 3
        }
    """
    HIGH_IMPORTANCE_THRESHOLD = 3

    label_map = {key: label for key, label in Feedback.PATTERN_CHOICES if key}
    faq_map = _build_faq_map(top_n=3)

    qs = (
        Feedback.objects.filter(sentiment=Feedback.NEGATIVE)
        .exclude(pattern_tag="")
        .values("pattern_tag")
        .annotate(count=Count("id"))
        .filter(count__gte=min_count)
        .order_by("-count")[:top_n]
    )

    return [
        {
            "pattern_tag": row["pattern_tag"],
            "label": label_map.get(row["pattern_tag"], row["pattern_tag"].title()),
            "count": row["count"],
            "is_high_importance": row["count"] >= HIGH_IMPORTANCE_THRESHOLD,
            "suggested_faqs": faq_map.get(row["pattern_tag"], []),
        }
        for row in qs
    ]


def high_importance_patterns(top_n: int = 10) -> list[dict]:
    """Convenience wrapper: only patterns that cross the high-importance threshold (3+)."""
    return negative_pattern_clusters(min_count=3, top_n=top_n)


# ---------------------------------------------------------------------------
# Auto-priority-adjustment: the feedback loop closes here.
# FAQ effectiveness triggers automatic priority changes.
# ---------------------------------------------------------------------------

HIGH_EFFECTIVENESS_THRESHOLD = 0.80  # 80% positive → bump priority
LOW_EFFECTIVENESS_THRESHOLD = 0.30   # 30% positive → lower priority
MIN_HIT_COUNT_FOR_ADJUSTMENT = 5     # Need 5+ total hits before adjusting


def get_priority_adjustments_needed() -> list[dict]:
    """
    Analyze all active FAQs and return a list of priority adjustment recommendations.

    Each item is a dict:
        {
            "faq": FAQ instance,
            "current_priority": int,
            "recommended_priority": int,
            "effectiveness_ratio": float,
            "total_hits": int,
            "reason": str,
        }

    Returns only FAQs where adjustment is needed and safe (sufficient hits).
    """
    adjustments = []

    for faq in FAQ.objects.filter(is_active=True):
        total_hits = faq.positive_hits + faq.negative_hits

        # Skip if not enough data.
        if total_hits < MIN_HIT_COUNT_FOR_ADJUSTMENT:
            continue

        effectiveness_ratio = faq.positive_hits / total_hits
        current_priority = faq.priority
        recommended_priority = current_priority

        reason = None

        # Rule 1: High effectiveness (80%+) → bump priority.
        if effectiveness_ratio >= HIGH_EFFECTIVENESS_THRESHOLD:
            if current_priority < FAQ.CRITICAL:
                recommended_priority = min(current_priority + 1, FAQ.CRITICAL)
                reason = f"High effectiveness ({effectiveness_ratio*100:.0f}%) — bumping priority"
        # Rule 2: Low effectiveness (30%-) → lower priority.
        elif effectiveness_ratio <= LOW_EFFECTIVENESS_THRESHOLD:
            if current_priority > FAQ.NORMAL:
                recommended_priority = max(current_priority - 1, FAQ.NORMAL)
                reason = f"Low effectiveness ({effectiveness_ratio*100:.0f}%) — lowering priority"

        # Only include if change is recommended.
        if recommended_priority != current_priority:
            adjustments.append({
                "faq": faq,
                "current_priority": current_priority,
                "recommended_priority": recommended_priority,
                "effectiveness_ratio": effectiveness_ratio,
                "total_hits": total_hits,
                "reason": reason,
            })

    return adjustments


def apply_priority_adjustments() -> dict:
    """
    Apply all recommended priority adjustments to FAQs in the database.

    Returns a summary dict:
        {
            "bumped": int,      # FAQs moved to higher priority
            "lowered": int,     # FAQs moved to lower priority
            "total": int,       # Total adjustments made
            "details": list,    # List of adjustment records
        }
    """
    adjustments_needed = get_priority_adjustments_needed()
    details = []

    for adj in adjustments_needed:
        faq = adj["faq"]
        old_priority = adj["current_priority"]
        new_priority = adj["recommended_priority"]

        faq.priority = new_priority
        faq.save(update_fields=["priority"])

        bumped = new_priority > old_priority
        details.append({
            "faq_id": faq.pk,
            "faq_question": faq.question[:80],  # First 80 chars
            "old_priority": old_priority,
            "new_priority": new_priority,
            "bumped": bumped,
            "effectiveness_ratio": adj["effectiveness_ratio"],
            "total_hits": adj["total_hits"],
            "reason": adj["reason"],
        })

    bumped_count = sum(1 for d in details if d["bumped"])
    lowered_count = len(details) - bumped_count

    return {
        "bumped": bumped_count,
        "lowered": lowered_count,
        "total": len(details),
        "details": details,
    }



def suggested_faqs_for_pattern(pattern_tag: str) -> list:
    """Return active FAQs linked to a specific pattern tag (alias for ranked_suggested_faqs)."""
    return ranked_suggested_faqs(pattern_tag)
