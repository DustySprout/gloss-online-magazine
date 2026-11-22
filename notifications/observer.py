"""
GoF: Observer — розсилка сповіщень.

EventPublisher (Subject) зберігає список спостерігачів і повідомляє їх про подію.
Спостерігачі (Observer) самі вирішують, як доставити сповіщення:
  * InAppObserver   — запис у БД (дзвіночок на сайті);
  * EmailObserver   — лист (у режимі розробки друкується в консоль).

GoF: Factory Method — NotificationFactory створює текст сповіщення
залежно від типу події, тож публікатор не знає деталей формулювань.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from .models import Notification


@dataclass
class Event:
    kind: str                     # одне з Notification.Kind
    payload: dict = field(default_factory=dict)


@dataclass
class Message:
    title: str
    text: str
    link: str = ""


# ---------- Factory Method ----------
class NotificationFactory:
    @staticmethod
    def create(event: Event) -> Message:
        p = event.payload
        if event.kind == Notification.Kind.NEW_ISSUE:
            return Message(f"Вийшов новий випуск: {p['title']}", "Свіжий номер журналу вже чекає на вас.", p.get("link", ""))
        if event.kind == Notification.Kind.EXCLUSIVE:
            return Message(f"Ексклюзив: {p['title']}", "Новий матеріал тільки для передплатників.", p.get("link", ""))
        if event.kind == Notification.Kind.PROMO:
            return Message(f"Акція від {p['partner']}", p["text"], p.get("link", ""))
        return Message(p.get("title", "Сповіщення"), p.get("text", ""), p.get("link", ""))


# ---------- Observer ----------
class Observer(ABC):
    @abstractmethod
    def update(self, user, event: Event, message: Message) -> None: ...


class InAppObserver(Observer):
    def update(self, user, event, message):
        Notification.objects.create(
            user=user, kind=event.kind, title=message.title, message=message.text, link=message.link
        )


class EmailObserver(Observer):
    def update(self, user, event, message):
        profile = getattr(user, "profile", None)
        if user.email and profile and profile.email_notifications:
            send_mail(message.title, message.text, None, [user.email], fail_silently=True)


class EventPublisher:
    """Subject. Визначає отримувачів і сповіщає всіх підписаних спостерігачів."""

    def __init__(self):
        self._observers: list[Observer] = []

    def attach(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer):
        self._observers.remove(observer)

    @staticmethod
    def _recipients(event: Event):
        users = get_user_model().objects.filter(is_active=True)
        if event.kind == Notification.Kind.EXCLUSIVE:
            from accounts.models import Profile
            return [u for u in users if Profile.for_user(u).is_premium]
        return list(users)

    def notify(self, event: Event):
        message = NotificationFactory.create(event)
        recipients = self._recipients(event)
        for user in recipients:
            for observer in self._observers:
                observer.update(user, event, message)
        return len(recipients)


def default_publisher() -> EventPublisher:
    publisher = EventPublisher()
    publisher.attach(InAppObserver())
    publisher.attach(EmailObserver())
    return publisher
