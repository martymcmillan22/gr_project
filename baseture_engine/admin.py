from django.contrib import admin
from .models import IndustryProfile, TierDefinition, GeneratedTier, SVEMTier, CCCPTier, PatternTemplate


@admin.register(IndustryProfile)
class IndustryProfileAdmin(admin.ModelAdmin):
    list_display = ('industry', 'name', 'created_at')
    search_fields = ('name', 'industry')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TierDefinition)
class TierDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier_level', 'mlas_color', 'industry', 'complexity', 'created_at')
    list_filter = ('tier_level', 'mlas_color', 'industry', 'complexity')
    search_fields = ('name', 'pattern_type')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Tier Classification', {
            'fields': ('tier_level', 'mlas_color', 'industry'),
        }),
        ('Basic Info', {
            'fields': ('name', 'description'),
        }),
        ('Pattern Definition', {
            'fields': ('pattern_type', 'complexity', 'required_fields', 'behaviors'),
        }),
        ('Tracking', {
            'fields': ('created_by', 'created_at', 'updated_at'),
        }),
    )


@admin.register(GeneratedTier)
class GeneratedTierAdmin(admin.ModelAdmin):
    list_display = ('seed_input', 'tier_definition', 'status', 'constraints_validated', 'created_at')
    list_filter = ('status', 'constraints_validated', 'tier_definition__mlas_color', 'created_at')
    search_fields = ('seed_input', 'tier_definition__name')
    readonly_fields = ('created_at', 'updated_at', 'validation_errors')
    fieldsets = (
        ('Input', {
            'fields': ('seed_input', 'tier_definition'),
        }),
        ('Generated Output', {
            'fields': ('output', 'rationale'),
            'classes': ('wide',),
        }),
        ('Validation', {
            'fields': ('status', 'constraints_validated', 'validation_errors'),
        }),
        ('Tracking', {
            'fields': ('created_by', 'approved_by', 'created_at', 'updated_at'),
        }),
    )


@admin.register(PatternTemplate)
class PatternTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'mlas_color', 'pattern_type', 'created_at')
    list_filter = ('mlas_color', 'pattern_type', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SVEMTier)
class SVEMTierAdmin(admin.ModelAdmin):
    list_display = ('branch_number', 'seed_input', 'parent_tier', 'status', 'constraints_validated', 'created_at')
    list_filter = ('status', 'constraints_validated', 'branch_number', 'created_at')
    search_fields = ('seed_input', 'parent_tier__seed_input')
    readonly_fields = ('created_at', 'updated_at', 'validation_errors')
    fieldsets = (
        ('Hierarchy', {
            'fields': ('parent_tier', 'branch_number'),
        }),
        ('Context', {
            'fields': ('seed_input', 'mlas_color', 'industry'),
        }),
        ('Generated Output', {
            'fields': ('output', 'rationale'),
            'classes': ('wide',),
        }),
        ('Validation', {
            'fields': ('status', 'constraints_validated', 'validation_errors'),
        }),
        ('Tracking', {
            'fields': ('created_by', 'created_at', 'updated_at'),
        }),
    )


@admin.register(CCCPTier)
class CCCPTierAdmin(admin.ModelAdmin):
    list_display = ('compartment_number', 'seed_input', 'parent_svem_tier', 'status', 'constraints_validated', 'created_at')
    list_filter = ('status', 'constraints_validated', 'compartment_number', 'created_at')
    search_fields = ('seed_input', 'parent_svem_tier__seed_input')
    readonly_fields = ('created_at', 'updated_at', 'validation_errors')
    fieldsets = (
        ('Hierarchy', {
            'fields': ('parent_svem_tier', 'compartment_number'),
        }),
        ('Context', {
            'fields': ('seed_input', 'mlas_color', 'industry'),
        }),
        ('Generated Output', {
            'fields': ('output', 'rationale'),
            'classes': ('wide',),
        }),
        ('Validation', {
            'fields': ('status', 'constraints_validated', 'validation_errors'),
        }),
        ('Tracking', {
            'fields': ('created_by', 'created_at', 'updated_at'),
        }),
    )
