from rest_framework import serializers

from ontology.models import Branch, Industry, Subject, SubIndustry, TemporalSlot


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "acronym", "order", "description"]


class BranchSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Branch
        fields = ["id", "subject", "subject_name", "name", "acronym", "order"]


class IndustrySerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    subject_name = serializers.CharField(source="branch.subject.name", read_only=True)

    class Meta:
        model = Industry
        fields = ["id", "branch", "branch_name", "subject_name", "name", "order"]


class SubIndustrySerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source="industry.name", read_only=True)
    branch_name = serializers.CharField(source="industry.branch.name", read_only=True)
    subject_name = serializers.CharField(source="industry.branch.subject.name", read_only=True)

    class Meta:
        model = SubIndustry
        fields = [
            "id",
            "industry",
            "industry_name",
            "branch_name",
            "subject_name",
            "name",
            "order",
        ]


class TemporalSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemporalSlot
        fields = ["id", "position", "tense", "color", "default_phase"]