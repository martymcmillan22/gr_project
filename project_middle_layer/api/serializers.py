from rest_framework import serializers

from project_middle_layer.models import ProjectNode


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
    slug = serializers.SlugField(max_length=120)
    name = serializers.CharField(max_length=255, trim_whitespace=True)
    semantic_intent = serializers.CharField(max_length=120, trim_whitespace=True)
    mlas_tier = serializers.CharField(max_length=120, trim_whitespace=True)
    btif_classification = serializers.CharField(max_length=120, trim_whitespace=True)
    semantic_tags = serializers.ListField(
        child=serializers.CharField(max_length=120, trim_whitespace=True),
        allow_empty=False,
    )
    metadata = serializers.DictField(required=False)

    def validate_semantic_tags(self, value):
        normalized = sorted({tag.strip().lower() for tag in value if tag.strip()})
        if not normalized:
            raise serializers.ValidationError("At least one semantic tag is required.")
        return normalized
