from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from content.models import Rubric

from .models import Collection, Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="Email", required=True)

    class Meta:
        model = User
        fields = ("username", "email")


class ProfileForm(forms.ModelForm):
    interests = forms.ModelMultipleChoiceField(
        queryset=Rubric.objects.all(), required=False,
        widget=forms.CheckboxSelectMultiple, label="Мої інтереси",
    )

    class Meta:
        model = Profile
        fields = ["bio", "interests", "recommendation_mode", "email_notifications"]


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["name", "description", "is_public"]
