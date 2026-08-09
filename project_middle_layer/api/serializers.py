from rest_framework import serializers

from project_middle_layer.models import ProjectNode


DEFAULT_MLAS_TIER = "Semantic Utility"
DEFAULT_BTIF_CLASSIFICATION = "ExpansionFlow"


def _pick_first_present(data, *keys, default=None):
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return default


class ProjectNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectNode
        fields = [
            "id",
            "slug",
            "name",
            "semantic_intent",
            "mlas_tier",
            "btif_classification",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProjectNodeWriteSerializer(serializers.Serializer):
    slug = serializers.SlugField(max_length=120, required=False)
    title = serializers.CharField(max_length=255, trim_whitespace=True, required=False)
    name = serializers.CharField(max_length=255, trim_whitespace=True, required=False)
    intent = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    semantic_intent = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    tier = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    mlas_tier = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    btif_classification = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    tags = serializers.ListField(child=serializers.CharField(max_length=120, trim_whitespace=True), required=False, allow_empty=False)
    semantic_tags = serializers.ListField(
        child=serializers.CharField(max_length=120, trim_whitespace=True),
        required=False,
        allow_empty=False,
    )
    metadata = serializers.DictField(required=False)

    def validate(self, attrs):
        title = _pick_first_present(attrs, "title", "name")
        intent = _pick_first_present(attrs, "intent", "semantic_intent")
        tier = _pick_first_present(attrs, "tier")
        semantic_tags = _pick_first_present(attrs, "semantic_tags", "tags", default=[])

        if not title:
            raise serializers.ValidationError({"title": "A title/name is required."})
        if not intent:
            raise serializers.ValidationError({"intent": "An intent/semantic_intent is required."})

        attrs["slug"] = attrs.get("slug") or title.strip().lower().replace(" ", "-")
        attrs["name"] = title
        attrs["semantic_intent"] = intent
        attrs["mlas_tier"] = _pick_first_present(attrs, "mlas_tier", default=DEFAULT_MLAS_TIER)
        attrs["btif_classification"] = _pick_first_present(attrs, "btif_classification", default=DEFAULT_BTIF_CLASSIFICATION)
        attrs["semantic_tags"] = semantic_tags
        attrs["visibility_tier"] = tier
        return attrs

    def validate_semantic_tags(self, value):
        normalized = sorted({tag.strip().lower() for tag in value if tag.strip()})
        if not normalized:
            raise serializers.ValidationError("At least one semantic tag is required.")
        return normalized


class ProjectWizardStartSerializer(serializers.Serializer):
    slug = serializers.SlugField(max_length=120, required=False)
    title = serializers.CharField(max_length=255, trim_whitespace=True, required=False)
    name = serializers.CharField(max_length=255, trim_whitespace=True, required=False)
    intent = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    semantic_intent = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    tier = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    mlas_tier = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    btif_classification = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False)

    def validate(self, attrs):
        title = _pick_first_present(attrs, "title", "name")
        intent = _pick_first_present(attrs, "intent", "semantic_intent")
        tier = _pick_first_present(attrs, "tier")

        if not title:
            raise serializers.ValidationError({"title": "A title/name is required."})
        if not intent:
            raise serializers.ValidationError({"intent": "An intent/semantic_intent is required."})

        attrs["slug"] = attrs.get("slug") or title.strip().lower().replace(" ", "-")
        attrs["name"] = title
        attrs["semantic_intent"] = intent
        attrs["mlas_tier"] = _pick_first_present(attrs, "mlas_tier", default=DEFAULT_MLAS_TIER)
        attrs["btif_classification"] = _pick_first_present(attrs, "btif_classification", default=DEFAULT_BTIF_CLASSIFICATION)
        attrs["visibility_tier"] = tier
        attrs["metadata"] = {
            **attrs.get("metadata", {}),
            **({"description": attrs["description"]} if attrs.get("description") else {}),
            **({"visibility_tier": tier} if tier else {}),
        }
        return attrs


class ProjectWizardTagsSerializer(serializers.Serializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=120, trim_whitespace=True),
        allow_empty=False,
        required=False,
    )
    semantic_tags = serializers.ListField(
        child=serializers.CharField(max_length=120, trim_whitespace=True),
        required=False,
        allow_empty=False,
    )
    metadata = serializers.DictField(required=False)

    def validate(self, attrs):
        value = _pick_first_present(attrs, "semantic_tags", "tags", default=[])
        normalized = sorted({tag.strip().lower() for tag in value if tag.strip()})
        if not normalized:
            raise serializers.ValidationError({"tags": "At least one semantic tag is required."})
        attrs["semantic_tags"] = normalized
        return attrs


class ProjectBatchCompileRequestSerializer(serializers.Serializer):
    projects = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
        max_length=100,
    )
    atomic = serializers.BooleanField(required=False, default=False)


class ProjectExportRequestSerializer(serializers.Serializer):
    scope = serializers.ChoiceField(choices=["all", "project"], required=False, default="all")
    project_slug = serializers.SlugField(max_length=120, required=False, allow_blank=True)
    include_history = serializers.BooleanField(required=False, default=False)
    download = serializers.BooleanField(required=False, default=False)
    max_items = serializers.IntegerField(required=False, min_value=1, max_value=500, default=100)

    def validate(self, attrs):
        scope = attrs.get("scope", "all")
        project_slug = (attrs.get("project_slug") or "").strip()

        if scope == "project" and not project_slug:
            raise serializers.ValidationError({"project_slug": "project_slug is required when scope=project."})

        attrs["project_slug"] = project_slug or None
        return attrs


class ProjectPipelineRunRequestSerializer(serializers.Serializer):
    pipeline_slug = serializers.SlugField(max_length=120)


class ProjectScheduleRunRequestSerializer(serializers.Serializer):
    schedule_slug = serializers.SlugField(max_length=120)


class IntegrationInboundSyncRequestSerializer(serializers.Serializer):
    payload = serializers.DictField()


class IntegrationOutboundSyncRequestSerializer(serializers.Serializer):
    scope = serializers.ChoiceField(choices=["all", "project"], required=False, default="all")
    project_slug = serializers.SlugField(max_length=120, required=False, allow_blank=True)
    include_history = serializers.BooleanField(required=False, default=False)
    max_items = serializers.IntegerField(required=False, min_value=1, max_value=500, default=100)

    def validate(self, attrs):
        scope = attrs.get("scope", "all")
        project_slug = (attrs.get("project_slug") or "").strip()
        if scope == "project" and not project_slug:
            raise serializers.ValidationError({"project_slug": "project_slug is required when scope=project."})
        attrs["project_slug"] = project_slug or None
        return attrs


class SemanticSearchRequestSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=255)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=200, default=50)

    def validate_q(self, value):
        text = (value or "").strip()
        if not text:
            raise serializers.ValidationError("q is required.")
        return text


class SemanticAnalyticsRequestSerializer(serializers.Serializer):
    branch_filter = serializers.CharField(max_length=120, required=False, allow_blank=True)
    tier_filter = serializers.CharField(max_length=120, required=False, allow_blank=True)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)

    def validate_branch_filter(self, value):
        return (value or "").strip().lower()

    def validate_tier_filter(self, value):
        return (value or "").strip().lower()


class SemanticVersionCommitRequestSerializer(serializers.Serializer):
    project_slug = serializers.SlugField(max_length=120)
    message = serializers.CharField(required=False, allow_blank=True, max_length=255)


class SemanticVersionCheckoutRequestSerializer(serializers.Serializer):
    version_id = serializers.IntegerField(min_value=1)


class SemanticMergeRequestSerializer(serializers.Serializer):
    left = serializers.DictField()
    right = serializers.DictField()
    base = serializers.DictField(required=False, default=dict)


class CollaborationSessionAcquireRequestSerializer(serializers.Serializer):
    project_slug = serializers.SlugField(max_length=120)
    force_takeover = serializers.BooleanField(required=False, default=False)
    lease_minutes = serializers.IntegerField(required=False, min_value=1, max_value=240, default=20)


class CollaborationSessionHeartbeatRequestSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(min_value=1)
    lease_minutes = serializers.IntegerField(required=False, min_value=1, max_value=240, default=20)


class CollaborationSessionReleaseRequestSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(min_value=1)


class MarketplaceInstallRequestSerializer(serializers.Serializer):
    item_slug = serializers.SlugField(max_length=120)
    requested_version = serializers.CharField(required=False, allow_blank=True, max_length=40)


class ExtensionApplyRequestSerializer(serializers.Serializer):
    extension_slug = serializers.SlugField(max_length=120)


class GatewayDispatchRequestSerializer(serializers.Serializer):
    route = serializers.CharField(max_length=120)
    requested_version = serializers.CharField(required=False, allow_blank=True, max_length=20)


class BtifPlusExportRequestSerializer(serializers.Serializer):
    project_slug = serializers.SlugField(max_length=120)


class BtifPlusValidateRequestSerializer(serializers.Serializer):
    payload = serializers.DictField()


class ExternalAgentRegisterRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    slug = serializers.SlugField(max_length=120)
    endpoint = serializers.URLField(max_length=500)
    capabilities = serializers.ListField(child=serializers.CharField(max_length=120), required=False, default=list)
    auth_token = serializers.CharField(required=False, allow_blank=True, max_length=255)
    status = serializers.ChoiceField(choices=["active", "disabled"], required=False, default="active")
    metadata = serializers.DictField(required=False, default=dict)


class ExternalAgentRunRequestSerializer(serializers.Serializer):
    agent_slug = serializers.SlugField(max_length=120)
    operation = serializers.CharField(max_length=120)
    payload = serializers.DictField(required=False, default=dict)


class CrossSyncRequestSerializer(serializers.Serializer):
    sync_type = serializers.ChoiceField(choices=["full", "delta", "version", "lineage", "analytics", "insight"])
    target_platform = serializers.CharField(max_length=120)
    project_slug = serializers.SlugField(max_length=120)


class CalculusTimelineRuntimeRequestSerializer(serializers.Serializer):
    selected_slot = serializers.IntegerField(required=False, min_value=1, max_value=16, default=1)
    completed_slots = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=16),
        required=False,
        default=list,
    )
    slot_content = serializers.DictField(required=False, default=dict)
    industry_context = serializers.DictField(required=False, default=dict)
    prior_slot_states = serializers.DictField(required=False, default=dict)

    def validate_completed_slots(self, value):
        unique = sorted({int(item) for item in value})
        return unique

    def validate_slot_content(self, value):
        normalized = {}
        for raw_key, raw_value in (value or {}).items():
            try:
                slot_index = int(raw_key)
            except (TypeError, ValueError):
                continue
            if slot_index < 1 or slot_index > 16:
                continue
            normalized[str(slot_index)] = str(raw_value or "")
        return normalized

    def validate_industry_context(self, value):
        context = dict(value or {})
        normalized = {
            "group": str(context.get("group", "") or ""),
            "industry": str(context.get("industry", "") or ""),
            "sub_industry": str(context.get("sub_industry", "") or ""),
            "slot_overrides": {},
        }

        overrides = context.get("slot_overrides", {})
        if isinstance(overrides, dict):
            for raw_key, raw_value in overrides.items():
                try:
                    slot_index = int(raw_key)
                except (TypeError, ValueError):
                    continue
                if slot_index < 1 or slot_index > 16 or not isinstance(raw_value, dict):
                    continue
                normalized["slot_overrides"][str(slot_index)] = {
                    "industry": str(raw_value.get("industry", "") or ""),
                    "sub_industry": str(raw_value.get("sub_industry", "") or ""),
                }

        return normalized

    def validate_prior_slot_states(self, value):
        normalized = {}
        for raw_key, raw_value in (value or {}).items():
            try:
                slot_index = int(raw_key)
            except (TypeError, ValueError):
                continue
            if slot_index < 1 or slot_index > 16 or not isinstance(raw_value, dict):
                continue
            normalized[str(slot_index)] = {
                "drift_score": raw_value.get("drift_score"),
                "alignment_score": raw_value.get("alignment_score"),
                "gate_locked": bool(raw_value.get("gate_locked", False)),
                "completed": bool(raw_value.get("completed", False)),
            }
        return normalized


class LfoEngineRequestSerializer(serializers.Serializer):
    selected_slot = serializers.IntegerField(required=False, min_value=1, max_value=16, default=1)
    completed_slots = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=16),
        required=False,
        default=list,
    )
    timeline_snapshot = serializers.DictField(required=False, default=dict)
    synthesis_snapshot = serializers.DictField(required=False, default=dict)
    trigger_count = serializers.IntegerField(required=False, min_value=0, default=0)
    feature_pathways = serializers.ListField(
        child=serializers.CharField(max_length=120, trim_whitespace=True),
        required=False,
        default=list,
    )

    def validate_completed_slots(self, value):
        return sorted({int(item) for item in value})

    def validate_feature_pathways(self, value):
        normalized = [str(item).strip().lower() for item in value if str(item).strip()]
        return normalized
