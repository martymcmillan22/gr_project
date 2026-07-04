from django import forms

from .models import ForumPost


class ForumPostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ["title", "body"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input", "placeholder": "Post title"}),
            "body": forms.Textarea(attrs={"class": "textarea", "rows": 5, "placeholder": "Write your discussion post..."}),
        }
