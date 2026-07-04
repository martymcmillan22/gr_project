from rest_framework import serializers

from platform_core.backend import BaseSerializer

from .models import HomepageAction, HomepageBackendItem, HomepageFlow, HomepagePreference, HomepageTask


class HomepageBackendItemSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = HomepageBackendItem


class HomepageTaskSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = HomepageTask


class HomepageFlowSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = HomepageFlow


class HomepagePreferenceSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = HomepagePreference


class HomepageActionSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = HomepageAction
