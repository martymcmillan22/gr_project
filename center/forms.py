from django import forms

from .models import CorporationItem


class CorporationItemForm(forms.ModelForm):
    class Meta:
        model = CorporationItem
        fields = ("title", "description", "item_type", "priority", "due_date")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }
