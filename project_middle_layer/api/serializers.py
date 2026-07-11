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
