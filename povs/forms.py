from django import forms
from .models import ExpoFact


class ExpoFactForm(forms.ModelForm):
    class Meta:
        model = ExpoFact
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Give your POV set a clear title...'}),
            'content': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': 'Present the facts, news, or context you want to respond to...',
            }),
        }

    def clean_title(self):
        value = self.cleaned_data['title'].strip()
        if not value:
            raise forms.ValidationError('Title cannot be empty.')
        return value

    def clean_content(self):
        value = self.cleaned_data['content'].strip()
        if not value:
            raise forms.ValidationError('Content cannot be empty.')
        return value


class FirstPersonForm(forms.Form):
    first_person = forms.CharField(
        label='Your first-person description',
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': 'In your own words, describe your personal perspective on these facts...',
        }),
        max_length=5000,
        strip=True,
    )

    def clean_first_person(self):
        value = self.cleaned_data['first_person'].strip()
        if not value:
            raise forms.ValidationError('Your description cannot be empty.')
        return value


class PredictionForm(forms.Form):
    prediction = forms.CharField(
        label='Your prediction',
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': 'Based on the facts and your perspective, what do you predict will happen...',
        }),
        max_length=5000,
        strip=True,
    )

    def clean_prediction(self):
        value = self.cleaned_data['prediction'].strip()
        if not value:
            raise forms.ValidationError('Your prediction cannot be empty.')
        return value


class NarrativeForm(forms.Form):
    narrative = forms.CharField(
        label='Play The Publicist — your narrative',
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': 'If you were their publicist, what would you advise them to do...',
        }),
        max_length=5000,
        strip=True,
    )

    def clean_narrative(self):
        value = self.cleaned_data['narrative'].strip()
        if not value:
            raise forms.ValidationError('Your narrative cannot be empty.')
        return value


class ProbableOutcomeForm(forms.Form):
    probable_outcome = forms.CharField(
        label='Probable outcome',
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': 'Given the publicist narrative above, what is the most probable outcome...',
        }),
        max_length=5000,
        strip=True,
    )

    def clean_probable_outcome(self):
        value = self.cleaned_data['probable_outcome'].strip()
        if not value:
            raise forms.ValidationError('The probable outcome cannot be empty.')
        return value
