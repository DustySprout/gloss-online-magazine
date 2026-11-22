from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Kind(models.TextChoices):
        NEW_ISSUE = "new_issue", "Новий випуск"
        EXCLUSIVE = "exclusive", "Ексклюзив для передплатників"
        PROMO = "promo", "Акція партнера"
        SYSTEM = "system", "Системне"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField("Тип", max_length=20, choices=Kind.choices)
    title = models.CharField("Заголовок", max_length=200)
    message = models.CharField("Текст", max_length=500)
    link = models.CharField("Посилання", max_length=300, blank=True)
    is_read = models.BooleanField("Прочитано", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Сповіщення"
        verbose_name_plural = "Сповіщення"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}: {self.title}"
