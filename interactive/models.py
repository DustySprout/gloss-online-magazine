from django.conf import settings
from django.db import models
from django.utils import timezone


class Poll(models.Model):
    question = models.CharField("Питання", max_length=250)
    article = models.ForeignKey(
        "content.Article", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="polls", verbose_name="Пов'язаний матеріал",
    )
    is_active = models.BooleanField("Активне", default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Опитування"
        verbose_name_plural = "Опитування"
        ordering = ["-created_at"]

    def __str__(self):
        return self.question

    @property
    def total_votes(self):
        return self.votes.count()

    def results(self):
        total = self.total_votes or 1
        return [
            {"option": o, "votes": o.votes.count(), "percent": round(o.votes.count() * 100 / total)}
            for o in self.options.all()
        ]


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField("Варіант", max_length=150)

    class Meta:
        verbose_name = "Варіант відповіді"
        verbose_name_plural = "Варіанти відповіді"

    def __str__(self):
        return self.text


class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("poll", "user")  # один голос на користувача
        verbose_name = "Голос"
        verbose_name_plural = "Голоси"


class Quiz(models.Model):
    class Kind(models.TextChoices):
        PERSONALITY = "personality", "Тест-характеристика («Який стиль вам підходить?»)"
        SCORE = "score", "Тест на знання (бали)"

    title = models.CharField("Назва тесту", max_length=200)
    description = models.TextField("Опис", blank=True)
    kind = models.CharField("Тип", max_length=20, choices=Kind.choices, default=Kind.PERSONALITY)
    rubric = models.ForeignKey("content.Rubric", on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField("Активний", default=True)

    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тести"

    def __str__(self):
        return self.title


class QuizOutcome(models.Model):
    """Можливий результат тесту-характеристики (напр. «Класичний стиль»)."""

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="outcomes")
    key = models.CharField("Код результату", max_length=30)
    title = models.CharField("Назва результату", max_length=120)
    description = models.TextField("Опис результату", blank=True)

    class Meta:
        verbose_name = "Результат тесту"
        verbose_name_plural = "Результати тесту"
        unique_together = ("quiz", "key")

    def __str__(self):
        return f"{self.quiz}: {self.title}"


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField("Питання", max_length=250)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Питання"
        verbose_name_plural = "Питання"
        ordering = ["order"]

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    text = models.CharField("Відповідь", max_length=200)
    outcome_key = models.CharField("Код результату (для тесту-характеристики)", max_length=30, blank=True)
    is_correct = models.BooleanField("Правильна (для тесту на знання)", default=False)

    class Meta:
        verbose_name = "Відповідь"
        verbose_name_plural = "Відповіді"

    def __str__(self):
        return self.text


class QuizResult(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="results")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_results")
    summary = models.CharField("Результат", max_length=200)
    score = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Результат проходження"
        verbose_name_plural = "Результати проходження"
        ordering = ["-created_at"]


class Comment(models.Model):
    article = models.ForeignKey("content.Article", on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField("Коментар", max_length=2000)
    is_visible = models.BooleanField("Показувати", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Коментар"
        verbose_name_plural = "Коментарі"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}: {self.text[:40]}"
