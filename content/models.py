from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


def unique_slug(instance, value, model):
    """Генерує унікальний slug (підтримує кирилицю через allow_unicode)."""
    base = slugify(value, allow_unicode=True)[:200] or "item"
    slug, n = base, 2
    while model.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


class Rubric(models.Model):
    name = models.CharField("Назва", max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, allow_unicode=True, blank=True)
    description = models.TextField("Опис", blank=True)
    color = models.CharField("Колір (HEX)", max_length=7, default="#c2185b")

    class Meta:
        verbose_name = "Рубрика"
        verbose_name_plural = "Рубрики"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, Rubric)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("rubric", args=[self.slug])

    def __str__(self):
        return self.name


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            status=Article.Status.PUBLISHED, published_at__lte=timezone.now()
        )


class Article(models.Model):
    class Kind(models.TextChoices):
        STANDARD = "standard", "Стаття"
        PHOTO = "photo", "Фотоісторія"
        VIDEO = "video", "Відеоматеріал"
        INTERVIEW = "interview", "Інтерв'ю"

    class Status(models.TextChoices):
        DRAFT = "draft", "Чернетка"
        PUBLISHED = "published", "Опубліковано"

    title = models.CharField("Заголовок", max_length=200)
    slug = models.SlugField(max_length=220, unique=True, allow_unicode=True, blank=True)
    rubric = models.ForeignKey(Rubric, on_delete=models.PROTECT, related_name="articles", verbose_name="Рубрика")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="articles", verbose_name="Автор",
    )
    kind = models.CharField("Тип", max_length=20, choices=Kind.choices, default=Kind.STANDARD)
    lead = models.CharField("Лід (короткий опис)", max_length=300)
    body = models.TextField("Текст")
    cover = models.ImageField("Обкладинка", upload_to="covers/", blank=True)
    video_url = models.URLField("Посилання на відео (YouTube embed)", blank=True)
    is_premium = models.BooleanField("Лише для преміум", default=False)
    partner = models.ForeignKey(
        "monetization.Partner", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sponsored_articles", verbose_name="Партнер (рекламна інтеграція)",
    )
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField("Дата публікації", default=timezone.now)
    views = models.PositiveIntegerField("Перегляди", default=0)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        verbose_name = "Матеріал"
        verbose_name_plural = "Матеріали"
        ordering = ["-published_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title, Article)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("article", args=[self.slug])

    def __str__(self):
        return self.title


class GalleryImage(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="gallery", verbose_name="Матеріал")
    image = models.ImageField("Фото", upload_to="gallery/")
    caption = models.CharField("Підпис", max_length=200, blank=True)
    is_exclusive = models.BooleanField("Ексклюзив для преміум", default=False)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Фото галереї"
        verbose_name_plural = "Галерея"
        ordering = ["order"]

    def __str__(self):
        return self.caption or f"Фото #{self.pk}"


class Issue(models.Model):
    """Випуск журналу. Спецвипуск «Журнал місяця» збирається через IssueBuilder."""

    title = models.CharField("Назва випуску", max_length=200)
    slug = models.SlugField(max_length=220, unique=True, allow_unicode=True, blank=True)
    number = models.PositiveIntegerField("Номер", unique=True)
    month = models.DateField("Місяць випуску")
    editor_note = models.TextField("Слово редактора", blank=True)
    cover = models.ImageField("Обкладинка", upload_to="issues/", blank=True)
    is_special = models.BooleanField("Спецвипуск («Журнал місяця»)", default=False)
    theme = models.CharField("Тема спецвипуску", max_length=120, blank=True)
    is_published = models.BooleanField("Опубліковано", default=False)
    articles = models.ManyToManyField(Article, through="IssueItem", related_name="issues", verbose_name="Матеріали")
    featured_poll = models.ForeignKey(
        "interactive.Poll", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Опитування випуску"
    )
    featured_quiz = models.ForeignKey(
        "interactive.Quiz", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Тест випуску"
    )

    class Meta:
        verbose_name = "Випуск"
        verbose_name_plural = "Випуски"
        ordering = ["-number"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, f"{self.number}-{self.title}", Issue)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("issue", args=[self.slug])

    def __str__(self):
        return f"№{self.number} — {self.title}"


class IssueItem(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="items")
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    order = models.PositiveIntegerField("Порядок", default=0)
    section = models.CharField("Розділ випуску", max_length=80, blank=True)

    class Meta:
        verbose_name = "Матеріал випуску"
        verbose_name_plural = "Матеріали випуску"
        ordering = ["order"]
        unique_together = ("issue", "article")
