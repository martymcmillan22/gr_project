from django.contrib import admin

from .models import DomainProfile


@admin.register(DomainProfile)
class DomainProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "board_corporation_label", "board_museum_label", "board_garden_label")
	search_fields = ("user__email", "user__username", "user__name")
	fieldsets = (
		("Account", {"fields": ("user",)}),
		(
			"Compartments",
			{
				"fields": (
					"compartment_1_label",
					"compartment_2_label",
					"compartment_3_label",
					"compartment_4_label",
					"compartment_5_label",
					"compartment_6_label",
					"compartment_7_label",
					"compartment_8_label",
					"compartment_9_label",
					"compartment_10_label",
					"compartment_11_label",
					"compartment_12_label",
				),
			},
		),
		(
			"Boards",
			{
				"fields": (
					"board_corporation_label",
					"board_museum_label",
					"board_garden_label",
				),
			},
		),
	)
