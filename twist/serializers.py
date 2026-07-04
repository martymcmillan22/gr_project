from rest_framework import serializers
from .models import CreativeIdea

class CreativeIdeaSerializer(serializers.ModelSerializer):
    content = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        max_length=5000,
    )
    tags = serializers.CharField(required=False, allow_blank=True, max_length=255)
    status = serializers.ChoiceField(
        choices=CreativeIdea.STATUS_CHOICES,
        required=False,
        default=CreativeIdea.STATUS_RAW,
    )

    def validate_content(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Content cannot be empty.')
        return cleaned

    def validate_tags(self, value):
        normalized_tags = [tag.strip() for tag in value.split(',') if tag.strip()]
        return ', '.join(normalized_tags)

    class Meta:
        model = CreativeIdea
        fields = ['id', 'content', 'tags', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']