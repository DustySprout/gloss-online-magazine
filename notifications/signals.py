"""Підписка на події моделей → виклик Observer-розсилки."""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from content.models import Article, Issue
from monetization.models import AdCampaign

from .models import Notification
from .observer import Event, default_publisher


def _was(instance, field):
    """Значення поля до збереження (None для нового об'єкта)."""
    if not instance.pk:
        return None
    old = type(instance).objects.filter(pk=instance.pk).values_list(field, flat=True).first()
    return old


@receiver(pre_save, sender=Issue)
def remember_issue_state(sender, instance, **kwargs):
    instance._was_published = bool(_was(instance, "is_published"))


@receiver(post_save, sender=Issue)
def issue_published(sender, instance, **kwargs):
    if instance.is_published and not getattr(instance, "_was_published", False):
        default_publisher().notify(Event(Notification.Kind.NEW_ISSUE, {
            "title": str(instance), "link": instance.get_absolute_url(),
        }))


@receiver(pre_save, sender=Article)
def remember_article_state(sender, instance, **kwargs):
    instance._old_status = _was(instance, "status")


@receiver(post_save, sender=Article)
def exclusive_published(sender, instance, **kwargs):
    became_published = (
        instance.status == Article.Status.PUBLISHED
        and getattr(instance, "_old_status", None) != Article.Status.PUBLISHED
    )
    if became_published and instance.is_premium:
        default_publisher().notify(Event(Notification.Kind.EXCLUSIVE, {
            "title": instance.title, "link": instance.get_absolute_url(),
        }))


@receiver(post_save, sender=AdCampaign)
def promo_created(sender, instance, created, **kwargs):
    if created and instance.is_promo and instance.is_active:
        default_publisher().notify(Event(Notification.Kind.PROMO, {
            "partner": instance.partner.name, "text": f"{instance.title}. {instance.text}",
            "link": instance.link,
        }))
