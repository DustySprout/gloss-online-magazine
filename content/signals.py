"""Нова публікація одразу потрапляє у свіжий номер і «Журнал місяця» (Observer через сигнали Django)."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Article
from .patterns import IssueDirector


@receiver(post_save, sender=Article, dispatch_uid="content_sync_issues")
def sync_issues_on_publish(sender, instance, **kwargs):
    if instance.status == Article.Status.PUBLISHED:
        IssueDirector.sync_current_issues()
