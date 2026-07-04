from collections import defaultdict
from datetime import timedelta
from urllib.parse import urlencode

from django.apps import apps
from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import connection, models
from django.utils import timezone


CONTROL_CENTER_APPS = [
    ("twist", "Twist", "/twist/"),
    ("center", "Center", "/center/"),
    ("domain", "Domain", "/domain/"),
    ("seeds", "Seeds", "/seeds/"),
    ("baseTrue_news", "News", "/basetruenews/"),
    ("homepage_backend", "Homepage", "/homepage/"),
    ("ontology", "Ontology", "/btif/api/"),
    ("career_app", "Career", "/career/"),
    ("forums", "Forums", "/forums/"),
]

REMAINING_DEEP_ANALYTICS_APPS = [
    ("domain", "Domain", "/domain/", ["DomainProfile"]),
    ("seeds", "Seeds", "/seeds/", ["Idea"]),
    ("baseTrue_news", "News", "/basetruenews/", ["Story"]),
    ("homepage_backend", "Homepage", "/homepage/", ["HomepageTask", "HomepageFlow"]),
    ("ontology", "Ontology", "/btif/api/", ["TemporalSlot"]),
    ("career_app", "Career", "/career/", ["CareerFilterPreset", "CareerPath"]),
    ("forums", "Forums", "/forums/", ["ForumPost"]),
]


def _with_pct(rows):
    peak = max((row["count"] for row in rows), default=1)
    for row in rows:
        row["pct"] = int((row["count"] / peak) * 100) if peak else 0
    return rows


def _build_daily_timeline(queryset, date_field, days=14):
    today = timezone.now().date()
    rows = []
    for index in range(days - 1, -1, -1):
        day = today - timedelta(days=index)
        count = queryset.filter(**{f"{date_field}__date": day}).count()
        rows.append({
            "day": day.strftime("%a"),
            "date": day.isoformat(),
            "count": count,
        })
    return _with_pct(rows)


def _admin_url(base_url, **params):
    if not params:
        return base_url
    return f"{base_url}?{urlencode(params)}"


def _admin_changelist_url(app_label, model_name):
    return f"/admin/{app_label}/{model_name.lower()}/"


def _pick_first_field(model, candidates):
    field_map = {field.name: field for field in model._meta.fields}
    for name in candidates:
        if name in field_map:
            return name, field_map[name]
    return None, None


def _top_user_rows(queryset, user_field, base_url, limit=5):
    user_id_key = f"{user_field}_id"
    username_key = f"{user_field}__username"
    rows = (
        queryset.values(user_id_key, username_key)
        .annotate(total=models.Count("id"))
        .order_by("-total")[:limit]
    )
    return [
        {
            "label": row[username_key] or f"User {row[user_id_key]}",
            "count": row["total"],
            "url": _admin_url(base_url, **{f"{user_field}__id__exact": row[user_id_key]}),
        }
        for row in rows
    ]


def _compute_health(row_count, activity_count, model_count, current_7d, previous_7d):
    score = 45

    if current_7d >= 14:
        score += 25
    elif current_7d >= 6:
        score += 16
    elif current_7d >= 1:
        score += 8

    if model_count >= 4:
        score += 8
    elif model_count >= 2:
        score += 4

    if row_count > 0:
        score += 6

    if previous_7d == 0 and current_7d > 0:
        trend = "up"
        score += 8
    elif current_7d > (previous_7d * 1.15):
        trend = "up"
        score += 10
    elif current_7d < (previous_7d * 0.85):
        trend = "down"
        score -= 12
    else:
        trend = "flat"

    attention_flags = []
    if activity_count == 0:
        attention_flags.append("No admin activity recorded")
    if current_7d == 0:
        attention_flags.append("No activity in the last 7 days")
    if row_count > 0 and current_7d == 0:
        attention_flags.append("Backlog may be stale")
    if previous_7d >= 4 and current_7d < previous_7d:
        attention_flags.append("Weekly activity is trending down")
    if row_count >= 100 and current_7d <= 3:
        attention_flags.append("High volume with low weekly throughput")

    score = max(0, min(100, score))
    if score >= 70:
        level = "high"
        label = "Green"
    elif score >= 45:
        level = "med"
        label = "Yellow"
    else:
        level = "low"
        label = "Red"

    trend_symbol = {
        "up": "↑",
        "flat": "→",
        "down": "↓",
    }.get(trend, "→")

    return {
        "score": score,
        "level": level,
        "label": label,
        "trend": trend,
        "trend_label": trend.upper(),
        "trend_symbol": trend_symbol,
        "attention_flags": attention_flags,
    }


def _build_twist_deep_analytics():
    base_url = "/admin/twist/creativeidea/"
    default_payload = {
        "base_url": base_url,
        "idea_total": 0,
        "ideas_last_7_days": 0,
        "ideas_last_30_days": 0,
        "ideas_per_week": 0.0,
        "seed_conversion_rate": 0.0,
        "idea_depth_score": 0.0,
        "quadrant_distribution": [
            {"name": "Red", "count": 0, "pct": 0},
            {"name": "Blue", "count": 0, "pct": 0},
            {"name": "Yellow", "count": 0, "pct": 0},
            {"name": "Green", "count": 0, "pct": 0},
        ],
        "top_contributors": [],
        "lifecycle": [
            {"label": "Raw", "count": 0, "url": _admin_url(base_url, status__exact="RAW")},
            {"label": "Seed", "count": 0, "url": _admin_url(base_url, status__exact="SEED")},
            {"label": "Business", "count": 0, "url": _admin_url(base_url, status__exact="BUSINESS")},
        ],
        "timeline": [],
    }

    try:
        creative_idea = apps.get_model("twist", "CreativeIdea")
    except LookupError:
        return default_payload

    try:
        idea_qs = creative_idea.objects.all()
    except Exception:
        return default_payload

    total = idea_qs.count()
    if total == 0:
        return default_payload

    seven_days_ago = timezone.now() - timedelta(days=7)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    ideas_last_7_days = idea_qs.filter(created_at__gte=seven_days_ago).count()
    ideas_last_30_days = idea_qs.filter(created_at__gte=thirty_days_ago).count()

    seed_count = idea_qs.filter(status="SEED").count()
    business_count = idea_qs.filter(status="BUSINESS").count()
    conversion_count = seed_count + business_count
    seed_conversion_rate = round((conversion_count / total) * 100, 1) if total else 0.0

    raw_count = idea_qs.filter(status="RAW").count()
    lifecycle = [
        {"label": "Raw", "count": raw_count, "url": _admin_url(base_url, status__exact="RAW")},
        {"label": "Seed", "count": seed_count, "url": _admin_url(base_url, status__exact="SEED")},
        {"label": "Business", "count": business_count, "url": _admin_url(base_url, status__exact="BUSINESS")},
    ]

    quadrant_map = {
        "Red": {"numbers": {1, 5, 9}, "keywords": {"raw", "spark", "concept", "vision", "problem", "challenge"}},
        "Blue": {"numbers": {2, 6, 10}, "keywords": {"build", "system", "flow", "structure", "logic", "model"}},
        "Yellow": {"numbers": {3, 7, 11}, "keywords": {"story", "community", "media", "news", "forum", "career"}},
        "Green": {"numbers": {4, 8, 12}, "keywords": {"growth", "launch", "business", "seed", "execution", "domain"}},
    }
    quadrant_counts = defaultdict(int)

    depth_score_total = 0.0
    timeline_rows = _build_daily_timeline(idea_qs, "created_at", days=14)
    for row in timeline_rows:
        row["url"] = _admin_url(base_url, created_at__date__exact=row["date"])

    for idea in idea_qs.only("content", "tags", "status"):
        content_len = len((idea.content or "").strip())
        tags = [t.strip().lower() for t in (idea.tags or "").split(",") if t.strip()]

        content_score = min((content_len / 280.0) * 60.0, 60.0)
        tag_score = min(len(tags) * 8.0, 40.0)
        depth_score_total += content_score + tag_score

        matched = False
        for tag in tags:
            if tag.isdigit():
                n = int(tag)
                for quadrant, rule in quadrant_map.items():
                    if n in rule["numbers"]:
                        quadrant_counts[quadrant] += 1
                        matched = True
                        break
                if matched:
                    continue

            for quadrant, rule in quadrant_map.items():
                if tag in rule["keywords"]:
                    quadrant_counts[quadrant] += 1
                    matched = True
                    break

        if not matched:
            status_defaults = {
                "RAW": "Red",
                "SEED": "Blue",
                "BUSINESS": "Green",
            }
            quadrant_counts[status_defaults.get(idea.status, "Yellow")] += 1

    idea_depth_score = round(depth_score_total / total, 1) if total else 0.0

    quadrant_distribution = []
    for name in ("Red", "Blue", "Yellow", "Green"):
        count = quadrant_counts[name]
        pct = int((count / total) * 100) if total else 0
        default_keyword = {
            "Red": "raw",
            "Blue": "build",
            "Yellow": "story",
            "Green": "business",
        }[name]
        quadrant_distribution.append(
            {
                "name": name,
                "count": count,
                "pct": pct,
                "url": _admin_url(base_url, q=default_keyword),
            }
        )

    top_contributors = _top_user_rows(idea_qs, "user", base_url)

    return {
        "base_url": base_url,
        "idea_total": total,
        "ideas_last_7_days": ideas_last_7_days,
        "ideas_last_30_days": ideas_last_30_days,
        "ideas_per_week": round((ideas_last_30_days / 30.0) * 7.0, 1),
        "seed_conversion_rate": seed_conversion_rate,
        "idea_depth_score": idea_depth_score,
        "quadrant_distribution": quadrant_distribution,
        "top_contributors": top_contributors,
        "lifecycle": lifecycle,
        "timeline": timeline_rows,
    }


def _build_center_deep_analytics():
    base_url = "/admin/center/corporationitem/"
    default_payload = {
        "base_url": base_url,
        "item_total": 0,
        "items_last_7_days": 0,
        "items_last_30_days": 0,
        "items_per_week": 0.0,
        "posting_rate": 0.0,
        "completion_rate": 0.0,
        "overdue_count": 0,
        "overdue_url": _admin_url(base_url),
        "status_breakdown": [],
        "work_breakdown": [],
        "priority_breakdown": [],
        "type_breakdown": [],
        "top_owners": [],
        "timeline": [],
    }

    try:
        corporation_item = apps.get_model("center", "CorporationItem")
    except LookupError:
        return default_payload

    try:
        item_qs = corporation_item.objects.all()
    except Exception:
        return default_payload

    total = item_qs.count()
    if total == 0:
        return default_payload

    today = timezone.now().date()
    seven_days_ago = timezone.now() - timedelta(days=7)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    items_last_7_days = item_qs.filter(created_at__gte=seven_days_ago).count()
    items_last_30_days = item_qs.filter(created_at__gte=thirty_days_ago).count()

    posted_count = item_qs.filter(status="posted").count()
    completion_done = item_qs.filter(work_status="done").count()
    overdue_count = item_qs.filter(due_date__lt=today).exclude(status="posted").count()

    status_labels = {
        "draft": "Draft",
        "review": "Review",
        "approved": "Approved",
        "posted": "Posted",
    }
    work_labels = {
        "todo": "To Do",
        "in_progress": "In Progress",
        "done": "Done",
    }
    priority_labels = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
    }
    type_labels = {
        "campaign": "Campaign",
        "event": "Event",
        "partnership": "Partnership",
        "general": "General",
    }

    status_breakdown = [
        {
            "label": status_labels[key],
            "count": item_qs.filter(status=key).count(),
            "url": _admin_url(base_url, status__exact=key),
        }
        for key in ("draft", "review", "approved", "posted")
    ]
    work_breakdown = [
        {
            "label": work_labels[key],
            "count": item_qs.filter(work_status=key).count(),
            "url": _admin_url(base_url, work_status__exact=key),
        }
        for key in ("todo", "in_progress", "done")
    ]
    priority_breakdown = [
        {
            "label": priority_labels[key],
            "count": item_qs.filter(priority=key).count(),
            "url": _admin_url(base_url, priority__exact=key),
        }
        for key in ("low", "medium", "high")
    ]
    type_breakdown = [
        {
            "label": type_labels[key],
            "count": item_qs.filter(item_type=key).count(),
            "url": _admin_url(base_url, item_type__exact=key),
        }
        for key in ("campaign", "event", "partnership", "general")
    ]

    return {
        "base_url": base_url,
        "item_total": total,
        "items_last_7_days": items_last_7_days,
        "items_last_30_days": items_last_30_days,
        "items_per_week": round((items_last_30_days / 30.0) * 7.0, 1),
        "posting_rate": round((posted_count / total) * 100, 1) if total else 0.0,
        "completion_rate": round((completion_done / total) * 100, 1) if total else 0.0,
        "overdue_count": overdue_count,
        "overdue_url": _admin_url(base_url, due_date__lt=today.isoformat()),
        "status_breakdown": status_breakdown,
        "work_breakdown": work_breakdown,
        "priority_breakdown": priority_breakdown,
        "type_breakdown": type_breakdown,
        "top_owners": _top_user_rows(item_qs, "owner", base_url),
        "timeline": [
            {
                **row,
                "url": _admin_url(base_url, created_at__date__exact=row["date"]),
            }
            for row in _build_daily_timeline(item_qs, "created_at", days=14)
        ],
    }


def _build_generic_app_deep_analytics(app_label, title, route, activity_count=0, preferred_model_names=None, health=None):
    default_payload = {
        "app_label": app_label,
        "title": title,
        "route": route,
        "activity_count": activity_count,
        "total_rows": 0,
        "model_count": 0,
        "rows_last_7_days": 0,
        "rows_last_30_days": 0,
        "rows_per_week": 0.0,
        "status_breakdown": [],
        "category_label": "Status",
        "top_contributors": [],
        "top_models": [],
        "timeline": [],
        "primary_model_label": "N/A",
        "health": health or {
            "score": 0,
            "level": "low",
            "label": "Red",
            "trend": "flat",
            "trend_label": "FLAT",
            "trend_symbol": "→",
            "attention_flags": [],
        },
    }

    model_classes = [model for model in apps.get_models() if model._meta.app_label == app_label]
    if not model_classes:
        return default_payload

    class_map = {model.__name__: model for model in model_classes}
    model_rows = []
    total_rows = 0
    for model in model_classes:
        try:
            count = model.objects.count()
        except Exception:
            continue
        total_rows += count
        model_rows.append(
            {
                "label": model.__name__,
                "count": count,
                "url": _admin_changelist_url(app_label, model.__name__),
                "model": model,
            }
        )

    if not model_rows:
        return default_payload

    model_rows.sort(key=lambda row: row["count"], reverse=True)
    preferred_model_names = preferred_model_names or []
    primary_model = None
    for name in preferred_model_names:
        if name in class_map:
            primary_model = class_map[name]
            break
    if primary_model is None:
        primary_model = model_rows[0]["model"]

    base_url = _admin_changelist_url(app_label, primary_model.__name__)
    primary_qs = primary_model.objects.all()

    timestamp_field, _ = _pick_first_field(primary_model, ["created_at", "created", "joined_at", "publish_at", "updated_at", "updated"])
    user_field, _ = _pick_first_field(primary_model, ["user", "owner", "author", "reviewer"])
    status_field, status_meta = _pick_first_field(
        primary_model,
        [
            "status",
            "forum_type",
            "feature",
            "item_type",
            "work_status",
            "tense",
            "default_phase",
            "market_status",
            "relationship_type",
            "degree_level_code",
            "salary_metric",
            "subject",
        ],
    )

    rows_last_7_days = 0
    rows_last_30_days = 0
    timeline = []
    if timestamp_field and primary_qs.exists():
        seven_days_ago = timezone.now() - timedelta(days=7)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        rows_last_7_days = primary_qs.filter(**{f"{timestamp_field}__gte": seven_days_ago}).count()
        rows_last_30_days = primary_qs.filter(**{f"{timestamp_field}__gte": thirty_days_ago}).count()
        timeline = [
            {
                **row,
                "url": _admin_url(base_url, **{f"{timestamp_field}__date__exact": row["date"]}),
            }
            for row in _build_daily_timeline(primary_qs, timestamp_field, days=14)
        ]

    top_contributors = _top_user_rows(primary_qs, user_field, base_url) if user_field else []

    status_breakdown = []
    if status_field:
        if getattr(status_meta, "choices", None):
            for value, label in status_meta.choices:
                status_breakdown.append(
                    {
                        "label": label,
                        "count": primary_qs.filter(**{status_field: value}).count(),
                        "url": _admin_url(base_url, **{f"{status_field}__exact": value}),
                    }
                )
        else:
            for row in primary_qs.values(status_field).annotate(total=models.Count("id")).order_by("-total")[:5]:
                value = row[status_field]
                status_breakdown.append(
                    {
                        "label": value or "Unknown",
                        "count": row["total"],
                        "url": _admin_url(base_url, **{f"{status_field}__exact": value}),
                    }
                )

    return {
        "app_label": app_label,
        "title": title,
        "route": route,
        "activity_count": activity_count,
        "total_rows": total_rows,
        "model_count": len(model_rows),
        "rows_last_7_days": rows_last_7_days,
        "rows_last_30_days": rows_last_30_days,
        "rows_per_week": round((rows_last_30_days / 30.0) * 7.0, 1) if rows_last_30_days else 0.0,
        "status_breakdown": status_breakdown,
        "category_label": status_field.replace("_", " ").title() if status_field else "Status",
        "top_contributors": top_contributors,
        "top_models": [{"label": row["label"], "count": row["count"], "url": row["url"]} for row in model_rows[:5]],
        "timeline": timeline,
        "primary_model_label": primary_model.__name__,
        "health": health or {
            "score": 0,
            "level": "low",
            "label": "Red",
            "trend": "flat",
            "trend_label": "FLAT",
            "trend_symbol": "→",
            "attention_flags": [],
        },
    }


def _build_semantic_cross_app_analytics():
    default_payload = {
        "stages": [
            {"key": "twist", "label": "Twist", "count": 0, "last_30_days": 0, "url": "/admin/twist/creativeidea/"},
            {"key": "seeds", "label": "Seeds", "count": 0, "last_30_days": 0, "url": "/admin/seeds/seed/"},
            {"key": "flow", "label": "Flow", "count": 0, "last_30_days": 0, "url": "/admin/homepage_backend/homepageflow/"},
            {"key": "taskboard", "label": "Taskboard", "count": 0, "last_30_days": 0, "url": "/admin/homepage_backend/homepagetask/"},
            {"key": "career", "label": "Career", "count": 0, "last_30_days": 0, "url": "/admin/career_app/careerfilterpreset/"},
        ],
        "links": [],
        "user_links": [],
        "overall_conversion_rate": 0.0,
        "bottleneck": {"label": "N/A", "dropoff_pct": 0},
        "alerts": [],
    }

    try:
        creative_idea = apps.get_model("twist", "CreativeIdea")
        seed_model = apps.get_model("seeds", "Seed")
        homepage_flow = apps.get_model("homepage_backend", "HomepageFlow")
        homepage_task = apps.get_model("homepage_backend", "HomepageTask")
        career_filter_preset = apps.get_model("career_app", "CareerFilterPreset")
    except Exception:
        return default_payload

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    twist_qs = creative_idea.objects.all()
    seeds_qs = seed_model.objects.all()
    flow_qs = homepage_flow.objects.all()
    task_qs = homepage_task.objects.all()
    career_qs = career_filter_preset.objects.all()

    stages = [
        {
            "key": "twist",
            "label": "Twist",
            "count": twist_qs.count(),
            "last_30_days": twist_qs.filter(created_at__gte=thirty_days_ago).count(),
            "url": "/admin/twist/creativeidea/",
        },
        {
            "key": "seeds",
            "label": "Seeds",
            "count": seeds_qs.count(),
            "last_30_days": seeds_qs.filter(created_at__gte=thirty_days_ago).count(),
            "url": "/admin/seeds/seed/",
        },
        {
            "key": "flow",
            "label": "Flow",
            "count": flow_qs.count(),
            "last_30_days": flow_qs.filter(created_at__gte=thirty_days_ago).count(),
            "url": "/admin/homepage_backend/homepageflow/",
        },
        {
            "key": "taskboard",
            "label": "Taskboard",
            "count": task_qs.count(),
            "last_30_days": task_qs.filter(created_at__gte=thirty_days_ago).count(),
            "url": "/admin/homepage_backend/homepagetask/",
        },
        {
            "key": "career",
            "label": "Career",
            "count": career_qs.count(),
            "last_30_days": career_qs.filter(created__gte=thirty_days_ago).count(),
            "url": "/admin/career_app/careerfilterpreset/",
        },
    ]

    max_stage_30d = max((stage["last_30_days"] for stage in stages), default=0)
    for stage in stages:
        stage["pct"] = int((stage["last_30_days"] / max_stage_30d) * 100) if max_stage_30d else 0

    links = []
    bottleneck = {"label": "N/A", "dropoff_pct": 0}
    for index in range(len(stages) - 1):
        current = stages[index]
        nxt = stages[index + 1]
        curr_count = current["count"]
        next_count = nxt["count"]
        conversion_pct = round((next_count / curr_count) * 100, 1) if curr_count else 0.0
        dropoff_count = max(curr_count - next_count, 0)
        dropoff_pct = int((dropoff_count / curr_count) * 100) if curr_count else 0
        link = {
            "from": current["label"],
            "to": nxt["label"],
            "conversion_pct": conversion_pct,
            "dropoff_count": dropoff_count,
            "dropoff_pct": dropoff_pct,
        }
        links.append(link)
        if dropoff_pct > bottleneck["dropoff_pct"]:
            bottleneck = {"label": f"{current['label']} -> {nxt['label']}", "dropoff_pct": dropoff_pct}

    twist_users = set(twist_qs.values_list("user_id", flat=True))
    seeds_users = set(seeds_qs.values_list("idea__user_id", flat=True))
    flow_users = set(flow_qs.values_list("owner_id", flat=True))
    task_users = set(task_qs.values_list("owner_id", flat=True))
    career_users = set(career_qs.values_list("user_id", flat=True))

    stage_users = [
        ("Twist", twist_users),
        ("Seeds", seeds_users),
        ("Flow", flow_users),
        ("Taskboard", task_users),
        ("Career", career_users),
    ]
    user_links = []
    for index in range(len(stage_users) - 1):
        left_name, left_users = stage_users[index]
        right_name, right_users = stage_users[index + 1]
        if left_users:
            overlap = len(left_users & right_users)
            overlap_pct = int((overlap / len(left_users)) * 100)
        else:
            overlap = 0
            overlap_pct = 0
        user_links.append(
            {
                "from": left_name,
                "to": right_name,
                "overlap": overlap,
                "overlap_pct": overlap_pct,
            }
        )

    overall_conversion_rate = round((stages[-1]["count"] / stages[0]["count"]) * 100, 1) if stages[0]["count"] else 0.0

    alerts = []
    if overall_conversion_rate < 20 and stages[0]["count"] > 0:
        alerts.append("End-to-end conversion is below 20%")
    if bottleneck["dropoff_pct"] >= 60:
        alerts.append(f"Severe drop-off at {bottleneck['label']}")
    if user_links and any(link["overlap_pct"] < 25 for link in user_links):
        alerts.append("Low user continuity across one or more pipeline transitions")

    return {
        "stages": stages,
        "links": links,
        "user_links": user_links,
        "overall_conversion_rate": overall_conversion_rate,
        "bottleneck": bottleneck,
        "alerts": alerts,
        "stage_peak": max_stage_30d,
    }


def _build_cross_dashboard_insights(app_control_panels, semantic_cross_app_analytics, activity_rows_14d, taskboard_rows, flow_rows):
    default_payload = {
        "state_label": "Stable",
        "state_note": "Cross-dashboard view is steady.",
        "pressure_proxy": 0.0,
        "cards": [],
        "signals": [],
        "links": [],
    }

    if not app_control_panels:
        return default_payload

    top_risk_panel = min(
        app_control_panels,
        key=lambda panel: (
            panel.get("health", {}).get("score", 0),
            len(panel.get("health", {}).get("attention_flags", [])),
        ),
    )
    top_strength_panel = max(
        app_control_panels,
        key=lambda panel: (
            panel.get("health", {}).get("score", 0),
            -len(panel.get("health", {}).get("attention_flags", [])),
        ),
    )
    forum_panel = next((panel for panel in app_control_panels if panel.get("app_label") == "forums"), None)

    activity_last_7 = sum(row.get("count", 0) for row in activity_rows_14d[-7:])
    activity_prev_7 = sum(row.get("count", 0) for row in activity_rows_14d[:7])
    activity_momentum = round(((activity_last_7 - activity_prev_7) / activity_prev_7) * 100, 1) if activity_prev_7 else 0.0

    average_health_score = round(
        sum(panel.get("health", {}).get("score", 0) for panel in app_control_panels) / len(app_control_panels),
        1,
    )
    pressure_proxy = round(
        max(
            0,
            min(
                100,
                (100 - average_health_score) * 0.42
                + len([panel for panel in app_control_panels if panel.get("health", {}).get("level") == "low"]) * 4
                + semantic_cross_app_analytics.get("bottleneck", {}).get("dropoff_pct", 0) * 0.3,
            ),
        ),
        1,
    )

    if pressure_proxy < 20:
        state_label = "Stable"
        state_note = "Portfolio conditions are balanced across dashboards."
    elif pressure_proxy < 40:
        state_label = "Watch"
        state_note = "One or more dashboards need closer attention."
    elif pressure_proxy < 65:
        state_label = "Elevated"
        state_note = "Lead indicators show growing cross-dashboard pressure."
    else:
        state_label = "Critical"
        state_note = "Cross-dashboard strain is concentrated and needs action."

    operator_balance = round((flow_rows / taskboard_rows) * 100, 1) if taskboard_rows else 0.0
    cards = [
        {
            "label": "Platform Health",
            "value": f"{sum(1 for panel in app_control_panels if panel['health']['level'] == 'high')} green / {sum(1 for panel in app_control_panels if panel['health']['level'] == 'med')} yellow / {sum(1 for panel in app_control_panels if panel['health']['level'] == 'low')} red",
            "secondary": f"{sum(len(panel['health']['attention_flags']) for panel in app_control_panels)} open flags",
            "url": "/admin/dashboard/",
        },
        {
            "label": "Executive Watch",
            "value": top_risk_panel.get("title", "N/A"),
            "secondary": f"Pressure proxy {pressure_proxy}",
            "url": "/admin/executive/",
        },
        {
            "label": "Operator Load",
            "value": f"{flow_rows}:{taskboard_rows}",
            "secondary": f"{operator_balance}% flow-to-task balance",
            "url": "/admin/operator/",
        },
        {
            "label": "Moderator Signal",
            "value": forum_panel.get("health", {}).get("label", "Unknown") if forum_panel else "Unknown",
            "secondary": forum_panel.get("health", {}).get("trend_label", "N/A") if forum_panel else "No forum panel",
            "url": "/admin/moderator/",
        },
        {
            "label": "Semantic Conversion",
            "value": f"{semantic_cross_app_analytics.get('overall_conversion_rate', 0)}%",
            "secondary": f"Bottleneck {semantic_cross_app_analytics.get('bottleneck', {}).get('label', 'N/A')}",
            "url": "#bt-analytics",
        },
    ]

    signals = [
        {
            "label": "Weekly momentum",
            "value": f"{activity_momentum}%",
            "secondary": f"{activity_last_7} actions vs {activity_prev_7} prior 7 days",
        },
        {
            "label": "Top strength",
            "value": top_strength_panel.get("title", "N/A"),
            "secondary": f"Score {top_strength_panel.get('health', {}).get('score', 0)}",
        },
        {
            "label": "Top risk",
            "value": top_risk_panel.get("title", "N/A"),
            "secondary": f"Score {top_risk_panel.get('health', {}).get('score', 0)}",
        },
    ]

    return {
        "state_label": state_label,
        "state_note": state_note,
        "pressure_proxy": pressure_proxy,
        "cards": cards,
        "signals": signals,
        "links": [
            {"label": "Platform", "url": "/admin/dashboard/"},
            {"label": "Executive", "url": "/admin/executive/"},
            {"label": "Operator", "url": "/admin/operator/"},
            {"label": "Moderator", "url": "/admin/moderator/"},
        ],
    }


def build_admin_metrics():
    model_metrics = []
    app_counts = defaultdict(int)
    taskboard_rows = 0
    flow_rows = 0

    for model in apps.get_models():
        if model._meta.app_label.startswith("django"):
            continue
        try:
            count = model.objects.count()
        except Exception:
            continue
        label = f"{model._meta.app_label}.{model.__name__}"
        model_metrics.append(
            {
                "label": label,
                "count": count,
            }
        )
        app_counts[model._meta.app_label] += count

        normalized = label.lower()
        if "task" in normalized:
            taskboard_rows += count
        if "flow" in normalized:
            flow_rows += count

    model_metrics.sort(key=lambda item: item["count"], reverse=True)
    app_metrics = sorted(
        [{"label": app_label, "count": value} for app_label, value in app_counts.items()],
        key=lambda item: item["count"],
        reverse=True,
    )

    today = timezone.now().date()
    activity_rows = []
    for index in range(6, -1, -1):
        day = today - timedelta(days=index)
        count = LogEntry.objects.filter(action_time__date=day).count()
        activity_rows.append({"day": day.strftime("%a"), "count": count})
    activity_rows = _with_pct(activity_rows)
    activity_rows_14d = _build_daily_timeline(LogEntry.objects.all(), "action_time", days=14)

    recent_actions = list(
        LogEntry.objects.select_related("user", "content_type").order_by("-action_time")[:20]
    )

    action_counts = defaultdict(int)
    for row in LogEntry.objects.values("content_type__app_label").annotate(total=models.Count("id")):
        app_label = row["content_type__app_label"]
        if app_label:
            action_counts[app_label] = row["total"]

    now = timezone.now()
    current_7d_start = now - timedelta(days=7)
    previous_7d_start = now - timedelta(days=14)
    app_activity_7d = defaultdict(int)
    app_activity_prev_7d = defaultdict(int)
    for app_label, _, _ in CONTROL_CENTER_APPS:
        app_activity_7d[app_label] = LogEntry.objects.filter(
            content_type__app_label=app_label,
            action_time__gte=current_7d_start,
        ).count()
        app_activity_prev_7d[app_label] = LogEntry.objects.filter(
            content_type__app_label=app_label,
            action_time__gte=previous_7d_start,
            action_time__lt=current_7d_start,
        ).count()

    app_metric_map = {item["label"]: item["count"] for item in app_metrics}
    app_control_panels = []
    for app_label, title, route in CONTROL_CENTER_APPS:
        model_count = len(
            [item for item in model_metrics if item["label"].startswith(f"{app_label}.")]
        )
        row_count = app_metric_map.get(app_label, 0)
        activity_count = action_counts.get(app_label, 0)
        current_7d = app_activity_7d[app_label]
        previous_7d = app_activity_prev_7d[app_label]
        health = _compute_health(
            row_count=row_count,
            activity_count=activity_count,
            model_count=model_count,
            current_7d=current_7d,
            previous_7d=previous_7d,
        )
        app_control_panels.append(
            {
                "app_label": app_label,
                "title": title,
                "route": route,
                "row_count": row_count,
                "activity_count": activity_count,
                "model_count": model_count,
                "current_7d": current_7d,
                "previous_7d": previous_7d,
                "health": health,
            }
        )

    app_panel_map = {panel["app_label"]: panel for panel in app_control_panels}
    health_legend = {
        "green": len([panel for panel in app_control_panels if panel["health"]["level"] == "high"]),
        "yellow": len([panel for panel in app_control_panels if panel["health"]["level"] == "med"]),
        "red": len([panel for panel in app_control_panels if panel["health"]["level"] == "low"]),
        "up": len([panel for panel in app_control_panels if panel["health"]["trend"] == "up"]),
        "flat": len([panel for panel in app_control_panels if panel["health"]["trend"] == "flat"]),
        "down": len([panel for panel in app_control_panels if panel["health"]["trend"] == "down"]),
        "flags": sum(len(panel["health"]["attention_flags"]) for panel in app_control_panels),
    }

    user_model = get_user_model()
    users_total = user_model.objects.count()
    users_staff = user_model.objects.filter(is_staff=True).count()
    user_date_field = None
    user_field_names = {field.name for field in user_model._meta.fields}
    for candidate in ("date_joined", "created_at", "created", "joined_at"):
        if candidate in user_field_names:
            user_date_field = candidate
            break
    user_growth_rows = []
    if user_date_field:
        user_growth_rows = _build_daily_timeline(user_model.objects.all(), user_date_field, days=14)
    twist_deep_analytics = _build_twist_deep_analytics()
    center_deep_analytics = _build_center_deep_analytics()
    semantic_cross_app_analytics = _build_semantic_cross_app_analytics()
    cross_dashboard_insights = _build_cross_dashboard_insights(
        app_control_panels,
        semantic_cross_app_analytics,
        activity_rows_14d,
        taskboard_rows,
        flow_rows,
    )
    remaining_app_deep_analytics = [
        _build_generic_app_deep_analytics(
            app_label,
            title,
            route,
            activity_count=action_counts.get(app_label, 0),
            preferred_model_names=preferred_models,
            health=app_panel_map.get(app_label, {}).get("health"),
        )
        for app_label, title, route, preferred_models in REMAINING_DEEP_ANALYTICS_APPS
    ]

    return {
        "users_total": users_total,
        "users_staff": users_staff,
        "roles_total": Group.objects.count(),
        "permissions_total": Permission.objects.count(),
        "model_metrics": model_metrics[:30],
        "app_metrics": app_metrics[:20],
        "diagnostics": {
            "debug": settings.DEBUG,
            "database_engine": connection.vendor,
            "installed_apps": len(settings.INSTALLED_APPS),
            "timezone": settings.TIME_ZONE,
        },
        "recent_actions": recent_actions,
        "activity_rows": activity_rows,
        "activity_rows_14d": activity_rows_14d,
        "user_growth_rows": user_growth_rows,
        "taskboard_rows": taskboard_rows,
        "flow_rows": flow_rows,
        "app_control_panels": app_control_panels,
        "twist_deep_analytics": twist_deep_analytics,
        "center_deep_analytics": center_deep_analytics,
        "semantic_cross_app_analytics": semantic_cross_app_analytics,
        "cross_dashboard_insights": cross_dashboard_insights,
        "remaining_app_deep_analytics": remaining_app_deep_analytics,
        "twist_health": app_panel_map.get("twist", {}).get("health"),
        "center_health": app_panel_map.get("center", {}).get("health"),
        "health_legend": health_legend,
    }
