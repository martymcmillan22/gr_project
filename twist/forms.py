from django import forms
from .models import CreativeIdea


class CreativeIdeaForm(forms.Form):
    content = forms.CharField(
        label='Your idea',
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Capture the idea while it is fresh...'}),
        max_length=5000,
        required=False,
        strip=True,
    )
    tags = forms.CharField(
        label='Tags',
        required=False,
        max_length=255,
        help_text='Optional. Separate tags with commas.',
        widget=forms.TextInput(attrs={'placeholder': 'client, urgent, follow-up'}),
        strip=True,
    )
    status = forms.ChoiceField(
        label='Stage',
        required=False,
        choices=CreativeIdea.STATUS_CHOICES,
        initial=CreativeIdea.STATUS_RAW,
    )

    def clean_content(self):
        content = self.cleaned_data['content'].strip()
        if not content:
            raise forms.ValidationError('Content cannot be empty.')
        return content

    def clean_tags(self):
        tags = self.cleaned_data['tags']
        normalized_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        return ', '.join(normalized_tags)

    def clean_status(self):
        status = self.cleaned_data.get('status') or CreativeIdea.STATUS_RAW
        valid_statuses = {choice[0] for choice in CreativeIdea.STATUS_CHOICES}
        if status not in valid_statuses:
            raise forms.ValidationError('Invalid status.')
        return status