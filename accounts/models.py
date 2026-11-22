from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    bio = models.CharField("Про себе", max_length=300, blank=True)
    interests = models.ManyToManyField("content.Rubric", blank=True, related_name="interested", verbose_name="Інтереси")
    saved_articles = models.ManyToManyField(
        "content.Article", blank=True, related_name="saved_by", verbose_name="Збережені матеріали"
    )
    recommendation_mode = models.CharField(
        "Режим рекомендацій", max_length=20, default="interests",
        choices=[("interests", "За інтересами"), ("popular", "Популярне"), ("fresh", "Найновіше")],
    )
    email_notifications = models.BooleanField("Сповіщення на email", default=True)

    class Meta:
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"

    def __str__(self):
        return f"Профіль {self.user.username}"

    @classmethod
    def for_user(cls, user):
        profile, _ = cls.objects.get_or_create(user=user)
        return profile

    @property
    def active_subscription(self):
        now = timezone.now()
        return (
            self.user.subscriptions.filter(is_active=True, starts_at__lte=now, ends_at__gte=now)
            .select_related("plan")
            .order_by("-ends_at")
            .first()
        )

    @property
    def is_premium(self):
        sub = self.active_subscription
        return bool(sub and sub.plan.exclusive_access)

    @property
    def sees_ads(self):
        sub = self.active_subscription
        return not (sub and sub.plan.ad_free)


class Collection(models.Model):
    """Власна підбірка користувача, напр. «Мої улюблені подорожі»."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="collections")
    name = models.CharField("Назва підбірки", max_length=120)
    description = models.CharField("Опис", max_length=300, blank=True)
    is_public = models.BooleanField("Публічна", default=False)
    articles = models.ManyToManyField("content.Article", blank=True, related_name="collections")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Підбірка"
        verbose_name_plural = "Підбірки"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
