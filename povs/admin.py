from django.contrib import admin
from .models import ExpoFact, POVResponse


@admin.register(ExpoFact)
class ExpoFactAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'content')
    ordering = ('-created_at',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(POVResponse)
class POVResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'expo_fact', 'has_blue', 'has_green', 'has_yellow', 'has_lime', 'created_at', 'updated_at')
    list_filter = ('expo_fact', 'created_at')
    search_fields = ('user__email', 'user__username', 'expo_fact__title')
    ordering = ('-updated_at',)
    readonly_fields = (
        'user', 'expo_fact',
        'first_person', 'first_person_at',
        'prediction', 'prediction_at',
        'narrative', 'narrative_at',
        'probable_outcome', 'probable_outcome_at',
        'created_at', 'updated_at',
    )

    def has_blue(self, obj):
        return bool(obj.first_person.strip())
    has_blue.boolean = True
    has_blue.short_description = 'Blue'

    def has_green(self, obj):
        return bool(obj.prediction.strip())
    has_green.boolean = True
    has_green.short_description = 'Green'

    def has_yellow(self, obj):
        return bool(obj.narrative.strip())
    has_yellow.boolean = True
    has_yellow.short_description = 'Yellow'

    def has_lime(self, obj):
        return bool(obj.probable_outcome.strip())
    has_lime.boolean = True
    has_lime.short_description = 'Lime'
