from django.conf import settings
from django.db import models

from .constants import (
	DOMAIN_BOARD_DEFINITIONS,
	DOMAIN_CELL_FIELD_BY_SLUG,
	DOMAIN_COMPARTMENT_DEFINITIONS,
	DOMAIN_DEFAULT_BOARD_VALUES,
	DOMAIN_DEFAULT_COMPARTMENT_VALUES,
	DOMAIN_DEFAULT_PROFILE_VALUES,
)


class DomainProfile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="domain_profile")
	compartment_1_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_COMPARTMENT_VALUES["compartment_1_label"])
	compartment_2_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_COMPARTMENT_VALUES["compartment_2_label"])
	compartment_3_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_COMPARTMENT_VALUES["compartment_3_label"])
	compartment_4_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_COMPARTMENT_VALUES["compartment_4_label"])
	compartment_5_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_COMPARTMENT_VALUES["compartment_5_label"])
	compartment_6_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_COMPARTMENT_VALUES["compartment_6_label"])
	compartment_7_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_COMPARTMENT_VALUES["compartment_7_label"])
	compartment_8_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_COMPARTMENT_VALUES["compartment_8_label"])
	compartment_9_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_COMPARTMENT_VALUES["compartment_9_label"])
	compartment_10_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_COMPARTMENT_VALUES["compartment_10_label"])
	compartment_11_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_COMPARTMENT_VALUES["compartment_11_label"])
	compartment_12_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_COMPARTMENT_VALUES["compartment_12_label"])
	board_corporation_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_BOARD_VALUES["board_corporation_label"])
	board_museum_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_BOARD_VALUES["board_museum_label"])
	board_garden_label = models.CharField(max_length=36, default=DOMAIN_DEFAULT_BOARD_VALUES["board_garden_label"])

	class Meta:
		ordering = ["user__username"]

	def __str__(self):
		return f"{self.user} domain profile"

	def save(self, *args, **kwargs):
		for field_name, default_value in DOMAIN_DEFAULT_PROFILE_VALUES.items():
			if not getattr(self, field_name):
				setattr(self, field_name, default_value)
		super().save(*args, **kwargs)

	def get_compartment_label(self, slug):
		field_name = DOMAIN_CELL_FIELD_BY_SLUG[slug]
		return getattr(self, field_name)

	def compartment_records(self):
		records = []
		for definition in DOMAIN_COMPARTMENT_DEFINITIONS:
			records.append({
				"slug": definition["slug"],
				"field_name": definition["field"],
				"default_label": definition["default"],
				"editable": definition["editable"],
				"display_limit": definition.get("display_limit"),
				"label": getattr(self, definition["field"]),
			})
		return records

	def board_records(self):
		records = []
		for definition in DOMAIN_BOARD_DEFINITIONS:
			records.append({
				"field_name": definition["field"],
				"default_label": definition["default"],
				"display_limit": definition.get("display_limit"),
				"label": getattr(self, definition["field"]),
			})
		return records
