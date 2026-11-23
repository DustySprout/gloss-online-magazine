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
        help_texts = {"username": "Латиниця або кирилиця, цифри та символи @ . + - _ (без пробілів), до 150 символів."}

    def clean_username(self):
        username = self.cleaned_data.get("username", "")
        if " " in username:
            suggestion = "_".join(username.split())
            raise forms.ValidationError(
                f"Ім'я користувача не може містити пробіли. Спробуйте, наприклад: {suggestion}"
            )
        return username


class ProfileForm(forms.ModelForm):
    MAX_AVATAR_MB = 3

    interests = forms.ModelMultipleChoiceField(
        queryset=Rubric.objects.all(), required=False,
        widget=forms.CheckboxSelectMultiple, label="Мої інтереси",
    )

    class Meta:
        model = Profile
        fields = ["avatar", "bio", "interests", "recommendation_mode", "email_notifications"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3, "maxlength": 300,
                                         "placeholder": "Кілька слів про себе: що читаєте, чим захоплюєтесь"}),
            "avatar": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar and hasattr(avatar, "size") and avatar.size > self.MAX_AVATAR_MB * 1024 * 1024:
            raise forms.ValidationError(f"Фото завелике: максимум {self.MAX_AVATAR_MB} МБ")
        return avatar


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["name", "description", "is_public"]
