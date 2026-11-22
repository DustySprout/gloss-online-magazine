from django.conf import settings
from django.db import models
from django.utils import timezone


class Plan(models.Model):
    name = models.CharField("Назва тарифу", max_length=80)
    price = models.DecimalField("Ціна, грн", max_digits=8, decimal_places=2)
    duration_days = models.PositiveIntegerField("Тривалість, днів", default=30)
    ad_free = models.BooleanField("Без реклами", default=True)
    exclusive_access = models.BooleanField("Ексклюзивні фото/відео", default=True)
    description = models.CharField("Опис", max_length=300, blank=True)
    is_active = models.BooleanField("Доступний", default=True)

    class Meta:
        verbose_name = "Тариф підписки"
        verbose_name_plural = "Тарифи підписки"
        ordering = ["price"]

    def __str__(self):
        return f"{self.name} ({self.price} грн)"


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Підписка"
        verbose_name_plural = "Підписки"
        ordering = ["-starts_at"]

    def __str__(self):
        return f"{self.user} — {self.plan.name} до {self.ends_at:%d.%m.%Y}"


class Partner(models.Model):
    name = models.CharField("Бренд-партнер", max_length=120)
    website = models.URLField("Сайт", blank=True)
    logo = models.ImageField("Логотип", upload_to="partners/", blank=True)
    description = models.TextField("Опис", blank=True)

    class Meta:
        verbose_name = "Партнер"
        verbose_name_plural = "Партнери"

    def __str__(self):
        return self.name


class AdCampaign(models.Model):
    """Рекламний блок або акція партнера."""

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="campaigns", verbose_name="Партнер")
    title = models.CharField("Заголовок", max_length=150)
    text = models.CharField("Текст", max_length=300)
    link = models.URLField("Посилання", blank=True)
    is_promo = models.BooleanField("Акція (надіслати сповіщення)", default=False)
    is_active = models.BooleanField("Активна", default=True)
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Рекламна кампанія / акція"
        verbose_name_plural = "Рекламні кампанії / акції"
        ordering = ["-starts_at"]

    def __str__(self):
        return f"{self.partner}: {self.title}"
