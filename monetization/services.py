"""
GoF: Facade — SubscriptionFacade приховує кілька кроків оформлення підписки
(перевірка тарифу, «оплата», продовження чинної підписки, сповіщення)
за одним простим методом subscribe().

GoF: Strategy (ще одне застосування) — вибір рекламного блоку для показу.
"""
import random
from abc import ABC, abstractmethod
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from notifications.models import Notification
from notifications.observer import InAppObserver, Event, Message

from .models import AdCampaign, Plan, Subscription


class PaymentGateway:
    """Імітація платіжної системи (у курсовій реальних платежів немає)."""

    def charge(self, user, amount) -> bool:
        return amount >= 0


class SubscriptionFacade:
    def __init__(self, gateway: PaymentGateway | None = None):
        self._gateway = gateway or PaymentGateway()

    @transaction.atomic
    def subscribe(self, user, plan_id: int) -> Subscription:
        plan = Plan.objects.get(pk=plan_id, is_active=True)
        if not self._gateway.charge(user, plan.price):
            raise ValueError("Оплата не пройшла")

        now = timezone.now()
        current = (
            Subscription.objects.filter(user=user, is_active=True, ends_at__gte=now)
            .order_by("-ends_at").first()
        )
        start = current.ends_at if current and current.plan_id == plan.id else now
        if current and current.plan_id != plan.id:
            current.is_active = False  # перехід на інший тариф
            current.save(update_fields=["is_active"])

        sub = Subscription.objects.create(
            user=user, plan=plan, starts_at=start if start > now else now,
            ends_at=start + timedelta(days=plan.duration_days), amount_paid=plan.price,
        )
        InAppObserver().update(
            user, Event(Notification.Kind.SYSTEM),
            Message("Підписку оформлено", f"Тариф «{plan.name}» діє до {sub.ends_at:%d.%m.%Y}.", "/profile/"),
        )
        return sub

    def cancel(self, user) -> int:
        return Subscription.objects.filter(user=user, is_active=True).update(is_active=False)


# ---------- вибір реклами ----------
class AdSelectionStrategy(ABC):
    @abstractmethod
    def pick(self, campaigns: list[AdCampaign], article=None) -> AdCampaign | None: ...


class RandomAdStrategy(AdSelectionStrategy):
    def pick(self, campaigns, article=None):
        return random.choice(campaigns) if campaigns else None


class PartnerFirstAdStrategy(AdSelectionStrategy):
    """Якщо матеріал має партнера — показуємо його ж рекламу."""

    def pick(self, campaigns, article=None):
        if article is not None and getattr(article, "partner_id", None):
            own = [c for c in campaigns if c.partner_id == article.partner_id]
            if own:
                return own[0]
        return RandomAdStrategy().pick(campaigns)


def active_campaigns():
    now = timezone.now()
    return [
        c for c in AdCampaign.objects.filter(is_active=True, starts_at__lte=now).select_related("partner")
        if c.ends_at is None or c.ends_at >= now
    ]
