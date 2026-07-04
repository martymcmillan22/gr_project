from django.contrib import admin

from .models import Business, CrossReference, Idea, Seed


@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "industry", "status", "updated_at")
	list_filter = ("status", "industry__group")
	search_fields = ("raw_content", "industry__name", "user__username")


@admin.register(Seed)
class SeedAdmin(admin.ModelAdmin):
	list_display = ("id", "idea", "germination_date", "updated_at")
	search_fields = ("idea__raw_content",)


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
	list_display = ("id", "brand_name", "market_status", "updated_at")
	search_fields = ("brand_name", "market_status")


@admin.register(CrossReference)
class CrossReferenceAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"source_business",
		"target_business",
		"relationship_type",
		"score",
		"created_at",
	)
	list_filter = ("relationship_type",)
	search_fields = ("source_business__brand_name", "target_business__brand_name")
