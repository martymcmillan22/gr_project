from rest_framework import serializers

from peringram.models import Industry

from .models import CrossReference, Idea


class IdeaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Idea
        fields = ["id", "industry", "raw_content", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class SeedSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    idea_id = serializers.IntegerField(read_only=True)
    polish_notes = serializers.DictField(read_only=True)
    germination_date = serializers.DateField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class SeedPromotionSerializer(serializers.Serializer):
    purpose = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    industry = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    audience = serializers.CharField(required=False, allow_blank=True, default="", trim_whitespace=True)
    narrative = serializers.CharField(required=False, allow_blank=True, default="", trim_whitespace=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="", trim_whitespace=True)
    identity_name = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    identity_type = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    identity_purpose = serializers.CharField(required=False, allow_blank=True, default="", trim_whitespace=True)
    identity_structure = serializers.CharField(required=False, allow_blank=True, default="", trim_whitespace=True)
    deliverables = serializers.CharField(required=False, allow_blank=True, default="", trim_whitespace=True)
    deliverable_structure = serializers.CharField(required=False, allow_blank=True, default="", trim_whitespace=True)
    deliverable_cadence = serializers.CharField(required=False, allow_blank=True, default="", trim_whitespace=True)
    metadata = serializers.DictField(required=False)


class BusinessSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    seed_id = serializers.IntegerField(read_only=True)
    brand_name = serializers.CharField(read_only=True)
    market_status = serializers.CharField(read_only=True)
    project_notes = serializers.DictField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ProjectActivationSerializer(serializers.Serializer):
    seed_id = serializers.IntegerField(required=True)
    project_name = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    market_status = serializers.CharField(required=False, allow_blank=False, default="draft", trim_whitespace=True)
    project_notes = serializers.DictField(required=False, default=dict)
    metadata = serializers.DictField(required=False, default=dict)


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
