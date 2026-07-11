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
