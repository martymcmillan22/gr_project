from django import forms

from .constants import (
	DOMAIN_BOARD_DEFINITIONS,
	DOMAIN_COMPARTMENT_DEFINITIONS,
	DOMAIN_DEFAULT_BOARD_VALUES,
	DOMAIN_DEFAULT_COMPARTMENT_VALUES,
	DOMAIN_EDITABLE_BOARD_FIELDS,
	DOMAIN_EDITABLE_COMPARTMENT_FIELDS,
)
from .models import DomainProfile


class DomainProfileForm(forms.ModelForm):
	class Meta:
		model = DomainProfile
		fields = [*DOMAIN_EDITABLE_COMPARTMENT_FIELDS, *DOMAIN_EDITABLE_BOARD_FIELDS]

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		for field_name in DOMAIN_EDITABLE_COMPARTMENT_FIELDS:
			field = self.fields[field_name]
			default_value = DOMAIN_DEFAULT_COMPARTMENT_VALUES[field_name]
			current_value = getattr(self.instance, field_name, "")
			field.required = False
			field.label = field.label or field_name.replace("_", " ").title()
			field.help_text = "Leave blank to keep the current value."
			field.widget.attrs.update({
				"class": "input",
				"maxlength": "36",
				"placeholder": default_value,
			})
			if current_value and current_value != default_value:
				field.initial = current_value

		for field_name in DOMAIN_EDITABLE_BOARD_FIELDS:
			field = self.fields[field_name]
			default_value = DOMAIN_DEFAULT_BOARD_VALUES[field_name]
			current_value = getattr(self.instance, field_name, "")
			field.required = False
			field.label = field.label or field_name.replace("_", " ").title()
			field.help_text = "Leave blank to keep the current value."
			field.widget.attrs.update({
				"class": "input",
				"maxlength": "36",
				"placeholder": default_value,
			})
			if current_value and current_value != default_value:
				field.initial = current_value

	def clean(self):
		cleaned_data = super().clean()

		for definition in DOMAIN_COMPARTMENT_DEFINITIONS:
			if not definition["editable"]:
				continue
			field_name = definition["field"]
			value = (cleaned_data.get(field_name) or "").strip()
			if not value:
				cleaned_data[field_name] = getattr(self.instance, field_name, "") or definition["default"]
				continue
			cleaned_data[field_name] = value

		for definition in DOMAIN_BOARD_DEFINITIONS:
			field_name = definition["field"]
			value = (cleaned_data.get(field_name) or "").strip()
			if not value:
				cleaned_data[field_name] = getattr(self.instance, field_name, "") or definition["default"]
				continue
			cleaned_data[field_name] = value

		return cleaned_data