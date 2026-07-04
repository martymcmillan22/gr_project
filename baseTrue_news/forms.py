from django import forms

from .models import NewsletterSubscriber


class NewsletterSignupForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ["email"]
