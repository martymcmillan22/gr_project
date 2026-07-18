from django import forms

from .markdown_parser import FORMAT_CHOICES


class StoryCreateForm(forms.Form):
    title = forms.CharField(
        max_length=300,
        label='Story Title',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a story title'}),
    )
    format = forms.ChoiceField(
        choices=list(FORMAT_CHOICES.items()),
        initial='movie',
        label='Starting Format',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )