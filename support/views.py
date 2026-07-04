import json

from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import FAQ, Feedback
from .services import classify_feedback_pattern, negative_pattern_clusters


def support_page(request):
    faqs = FAQ.objects.filter(is_active=True)
    confusion_areas = negative_pattern_clusters() if request.user.is_staff else []

    # Build a serialisable FAQ-by-pattern map for the JS feedback widget.
    # All users see this so the "helpful FAQ" suggestion works after a 👎.
    from .services import _build_faq_map
    faq_by_pattern = {
        tag: [{"pk": faq.pk, "question": faq.question} for faq in faqs_list]
        for tag, faqs_list in _build_faq_map().items()
    }

    return render(request, "support/support_page.html", {
        "faqs": faqs,
        "confusion_areas": confusion_areas,
        "faq_by_pattern": faq_by_pattern,
    })


@require_POST
def submit_feedback(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    sentiment = data.get("sentiment", "").strip()
    if sentiment not in (Feedback.POSITIVE, Feedback.NEGATIVE):
        return JsonResponse({"error": "Invalid sentiment."}, status=400)

    text = data.get("text", "").strip()[:2000]  # cap input length
    page_url = data.get("page_url", "").strip()[:500]
    viewed_faq_ids = data.get("viewed_faq_ids", [])  # list of FAQ pks clicked

    # Only store text for negative feedback
    if sentiment == Feedback.POSITIVE:
        text = ""

    user = request.user if request.user.is_authenticated else None

    # Increment FAQ positive_hits for any viewed FAQs.
    if viewed_faq_ids:
        for faq_id in viewed_faq_ids:
            FAQ.objects.filter(pk=faq_id).update(positive_hits=F('positive_hits') + 1)

    # Increment negative_hits only for negative feedback.
    if sentiment == Feedback.NEGATIVE:
        for faq_id in viewed_faq_ids:
            FAQ.objects.filter(pk=faq_id).update(negative_hits=F('negative_hits') + 1)

    # Auto-classify the feedback pattern from text.
    pattern_tag = classify_feedback_pattern(text)

    Feedback.objects.create(
        sentiment=sentiment,
        text=text,
        page_url=page_url,
        user=user,
        pattern_tag=pattern_tag,
    )
    return JsonResponse({"status": "ok"})
