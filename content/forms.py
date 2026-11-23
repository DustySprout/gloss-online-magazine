"""Форма, через яку звичайний користувач публікує матеріал прямо з сайту."""
import re

from django import forms

from .models import Article, Rubric

YOUTUBE_ID = re.compile(r"(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([\w-]{11})")


def to_youtube_embed(url: str) -> str:
    """Будь-яке посилання YouTube → адреса для вбудовування (youtube.com/embed/ID)."""
    match = YOUTUBE_ID.search(url or "")
    return f"https://www.youtube.com/embed/{match.group(1)}" if match else url


class ArticleForm(forms.ModelForm):
    MAX_COVER_MB = 5

    rubric = forms.ModelChoiceField(queryset=Rubric.objects.all(), label="Рубрика", empty_label="Оберіть рубрику")
    kind = forms.ChoiceField(choices=Article.Kind.choices, label="Тип матеріалу")

    class Meta:
        model = Article
        fields = ["title", "rubric", "kind", "lead", "body", "cover", "video_url"]
        labels = {
            "title": "Заголовок",
            "lead": "Короткий опис (лід)",
            "body": "Текст",
            "cover": "Обкладинка",
            "video_url": "Посилання на відео YouTube",
        }
        help_texts = {
            "lead": "1–2 речення, які видно в картці статті.",
            "body": "Абзаци розділяйте порожнім рядком.",
            "video_url": "Обов'язково для типу «Відеоматеріал». Можна вставити звичайне посилання з YouTube.",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Наприклад: 5 місць у Карпатах для зимових вихідних"}),
            "lead": forms.Textarea(attrs={"rows": 2, "maxlength": 300}),
            "body": forms.Textarea(attrs={"rows": 14}),
            "cover": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "video_url": forms.URLInput(attrs={"placeholder": "https://www.youtube.com/watch?v=..."}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 5:
            raise forms.ValidationError("Заголовок занадто короткий: мінімум 5 символів.")
        return title

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if len(body) < 100:
            raise forms.ValidationError(f"Текст занадто короткий: мінімум 100 символів (зараз {len(body)}).")
        return body

    def clean_cover(self):
        cover = self.cleaned_data.get("cover")
        if cover and hasattr(cover, "size") and cover.size > self.MAX_COVER_MB * 1024 * 1024:
            raise forms.ValidationError(f"Обкладинка завелика: максимум {self.MAX_COVER_MB} МБ.")
        return cover

    def clean(self):
        data = super().clean()
        url = data.get("video_url", "")
        if url:
            data["video_url"] = to_youtube_embed(url)
        if data.get("kind") == Article.Kind.VIDEO and not url:
            self.add_error("video_url", "Для відеоматеріалу потрібне посилання на відео.")
        return data
