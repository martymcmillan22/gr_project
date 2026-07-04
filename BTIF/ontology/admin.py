from django.contrib import admin
from .models import Branch, Industry, Subject, SubIndustry, TemporalSlot


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
	list_display = ("order", "name", "acronym")
	search_fields = ("name", "acronym")
	ordering = ("order",)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
	list_display = ("subject", "order", "name", "acronym")
	list_filter = ("subject",)
	search_fields = ("name", "acronym", "subject__name")
	ordering = ("subject__order", "order")


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
	list_display = ("branch", "order", "name")
	list_filter = ("branch__subject", "branch")
	search_fields = ("name", "branch__name")
	ordering = ("branch__subject__order", "branch__order", "order")


@admin.register(SubIndustry)
class SubIndustryAdmin(admin.ModelAdmin):
	list_display = ("industry", "order", "name")
	list_filter = ("industry__branch__subject", "industry__branch", "industry")
	search_fields = ("name", "industry__name")
	ordering = ("industry__branch__subject__order", "industry__branch__order", "industry__order", "order")


@admin.register(TemporalSlot)
class TemporalSlotAdmin(admin.ModelAdmin):
	list_display = ("position", "tense", "color", "default_phase")
	list_filter = ("tense", "default_phase")
	ordering = ("position",)
