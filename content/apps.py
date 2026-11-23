from django.apps import AppConfig


class ContentConfig(AppConfig):
    name = "content"
    verbose_name = "Контент журналу"

    def ready(self):
        from . import signals  # noqa: F401  (реєстрація обробників)
