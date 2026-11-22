"""GoF: Singleton — глобальні налаштування журналу існують в одному екземплярі."""
from django.db import models


class SingletonModel(models.Model):
    """Абстрактна модель-одинак: у таблиці завжди лише один запис (pk=1)."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Єдиний екземпляр видаляти не можна
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SiteSettings(SingletonModel):
    magazine_name = models.CharField("Назва журналу", max_length=100, default="GLOSS")
    tagline = models.CharField(
        "Слоган", max_length=200, default="Спорт, мода, подорожі та стиль життя"
    )
    show_ads_to_free_users = models.BooleanField("Показувати рекламу безкоштовним", default=True)
    free_articles_per_month = models.PositiveIntegerField("Безкоштовних статей на місяць", default=20)
    contact_email = models.EmailField("Контактний email", default="editor@gloss.ua")

    class Meta:
        verbose_name = "Налаштування журналу"
        verbose_name_plural = "Налаштування журналу"

    def __str__(self):
        return "Налаштування журналу"
