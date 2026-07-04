from rest_framework import serializers

from peringram.models import Industry

from .models import CrossReference, Idea


class IdeaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Idea
        fields = ["id", "industry", "raw_content", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class IdeaCaptureSerializer(serializers.Serializer):
    industry_id = serializers.IntegerField(required=True)
    raw_content = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    compartment_id = serializers.IntegerField(required=False)
    metadata = serializers.DictField(required=False)

    def validate_industry_id(self, value):
        if not Industry.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid industry ID.")
        return value

    def validate_raw_content(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Raw content cannot be empty.")
        return cleaned


class CrossReferenceSerializer(serializers.ModelSerializer):
    source_industry_id = serializers.IntegerField(source="source_business.seed.idea.industry_id", read_only=True)
    target_industry_id = serializers.IntegerField(source="target_business.seed.idea.industry_id", read_only=True)

    class Meta:
        model = CrossReference
        fields = [
            "id",
            "source_business",
            "target_business",
            "source_industry_id",
            "target_industry_id",
            "relationship_type",
            "score",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
