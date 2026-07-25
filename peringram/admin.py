from django.contrib import admin

from .models import (
	BaseTrueSquareRootMap,
	ConvectionCompartment,
	Industry,
	IndustryGroup,
	LatticeCompartment,
	Recycle3Profile,
	SubIndustry,
)


@admin.register(Recycle3Profile)
class Recycle3ProfileAdmin(admin.ModelAdmin):
	list_display = (
		"user",
		"corporation_rnd_pct",
		"people_qcqa_pct",
		"government_infra_pct",
		"isea_pct",
		"updated_at",
	)
	search_fields = ("user__username", "user__email")


@admin.register(BaseTrueSquareRootMap)
class BaseTrueSquareRootMapAdmin(admin.ModelAdmin):
	list_display = ("territory_name", "user", "updated_at")
	search_fields = ("territory_name", "user__username", "user__email")


@admin.register(IndustryGroup)
class IndustryGroupAdmin(admin.ModelAdmin):
	list_display = ("code", "name", "sector")
	list_filter = ("sector",)
	search_fields = ("name",)


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
	list_display = ("name", "group", "code")
	list_filter = ("group__sector",)
	search_fields = ("name",)


@admin.register(SubIndustry)
class SubIndustryAdmin(admin.ModelAdmin):
	list_display = ("name", "industry", "code")
	list_filter = ("industry__group__sector",)
	search_fields = ("name",)


@admin.register(ConvectionCompartment)
class ConvectionCompartmentAdmin(admin.ModelAdmin):
	list_display = ("compartment_index", "world_clock_hour", "label", "lattice_coordinate")
	search_fields = ("label", "lattice_coordinate")


@admin.register(LatticeCompartment)
class LatticeCompartmentAdmin(admin.ModelAdmin):
	list_display = ("index", "color", "time_frame", "capacity", "category")
	list_filter = ("time_frame",)
	search_fields = ("category", "color")
