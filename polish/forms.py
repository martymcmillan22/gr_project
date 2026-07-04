from django import forms

from .models import PolishTask, SectorAgenda, PolishReminderPreference


class PolishTaskForm(forms.ModelForm):
    class Meta:
        model = PolishTask
        fields = ("title", "details", "due_date")
        widgets = {
            "details": forms.Textarea(attrs={"rows": 3}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }


class SectorAgendaForm(forms.ModelForm):
    class Meta:
        model = SectorAgenda
        fields = ("sector_name", "idea", "objective")


class PolishReminderPreferenceForm(forms.ModelForm):
    class Meta:
        model = PolishReminderPreference
        fields = ("enabled",)
