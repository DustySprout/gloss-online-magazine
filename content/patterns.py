"""
GoF-патерни підсистеми контенту:

  * Factory Method — ArticleCreator та його підкласи створюють матеріали різних типів.
  * Builder        — IssueBuilder + IssueDirector покроково збирають випуск / «Журнал місяця».
  * Proxy          — ArticleAccessProxy контролює доступ до преміум-контенту.
  * Decorator      — ArticleRenderer + декоратори додають рекламу і бейдж партнера.
"""
from abc import ABC, abstractmethod
from datetime import date

from django.db import transaction
from django.utils import timezone
from django.utils.html import escape, linebreaks

from .models import Article, Issue, IssueItem


# =====================================================================
# Factory Method
# =====================================================================
class ArticleCreator(ABC):
    """Творець. Шаблон створення спільний, конкретний тип визначають підкласи."""

    kind: str = Article.Kind.STANDARD

    def create(self, *, title, rubric, lead, body, author=None, **extra) -> Article:
        article = Article(title=title, rubric=rubric, lead=lead, body=body, author=author, kind=self.kind)
        self.configure(article, **extra)
        article.save()
        return article

    @abstractmethod
    def configure(self, article: Article, **extra) -> None:
        """Налаштування, специфічні для типу матеріалу."""


class StandardArticleCreator(ArticleCreator):
    kind = Article.Kind.STANDARD

    def configure(self, article, **extra):
        article.is_premium = extra.get("is_premium", False)


class PhotoStoryCreator(ArticleCreator):
    kind = Article.Kind.PHOTO

    def configure(self, article, **extra):
        article.is_premium = extra.get("is_premium", False)
        if extra.get("cover"):
            article.cover = extra["cover"]


class VideoStoryCreator(ArticleCreator):
    kind = Article.Kind.VIDEO

    def configure(self, article, **extra):
        url = extra.get("video_url", "")
        if not url:
            raise ValueError("Відеоматеріал потребує посилання на відео")
        article.video_url = url
        article.is_premium = extra.get("is_premium", True)  # відео за замовчуванням — ексклюзив


class InterviewCreator(ArticleCreator):
    kind = Article.Kind.INTERVIEW

    def configure(self, article, **extra):
        guest = extra.get("guest")
        if guest and guest not in article.title:
            article.title = f"{guest}: {article.title}"
        article.is_premium = extra.get("is_premium", False)


CREATORS = {
    Article.Kind.STANDARD: StandardArticleCreator,
    Article.Kind.PHOTO: PhotoStoryCreator,
    Article.Kind.VIDEO: VideoStoryCreator,
    Article.Kind.INTERVIEW: InterviewCreator,
}


def get_creator(kind: str) -> ArticleCreator:
    try:
        return CREATORS[kind]()
    except KeyError:
        raise ValueError(f"Невідомий тип матеріалу: {kind}")


# =====================================================================
# Builder
# =====================================================================
class IssueBuilder:
    """Покроково збирає випуск журналу; build() зберігає все однією транзакцією."""

    def __init__(self, number: int, title: str):
        self._data = {"number": number, "title": title, "month": date.today().replace(day=1)}
        self._items: list[tuple[Article, str]] = []
        self._publish = False

    def for_month(self, month: date):
        self._data["month"] = month.replace(day=1)
        return self

    def with_editor_note(self, text: str):
        self._data["editor_note"] = text
        return self

    def as_special(self, theme: str):
        self._data["is_special"] = True
        self._data["theme"] = theme
        return self

    def add_article(self, article: Article, section: str = ""):
        self._items.append((article, section))
        return self

    def add_articles(self, articles, section: str = ""):
        for a in articles:
            self.add_article(a, section)
        return self

    def with_poll(self, poll):
        self._data["featured_poll"] = poll
        return self

    def with_quiz(self, quiz):
        self._data["featured_quiz"] = quiz
        return self

    def published(self, flag: bool = True):
        self._publish = flag
        return self

    @transaction.atomic
    def build(self) -> Issue:
        if not self._items:
            raise ValueError("Випуск повинен містити хоча б один матеріал")
        issue = Issue.objects.create(**self._data, is_published=False)
        for order, (article, section) in enumerate(self._items, start=1):
            IssueItem.objects.create(issue=issue, article=article, order=order, section=section)
        if self._publish:
            issue.is_published = True
            issue.save()  # тут спрацює Observer → сповіщення «Новий випуск»
        return issue


class IssueDirector:
    """Знає типові «рецепти» випусків і керує будівельником."""

    @staticmethod
    def magazine_of_the_month(number: int, theme: str, poll=None, quiz=None, publish=True) -> Issue:
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        best = Article.published.filter(published_at__gte=month_start).order_by("-views")[:6]
        if not best:
            best = Article.published.order_by("-views")[:6]
        builder = (
            IssueBuilder(number, f"Журнал місяця: {theme}")
            .as_special(theme)
            .with_editor_note(f"Найкращі матеріали місяця на тему «{theme}», обрані редакцією та читачами.")
            .add_articles(best[:1], "Головна історія")
            .add_articles(best[1:], "Найпопулярніше")
            .published(publish)
        )
        if poll:
            builder.with_poll(poll)
        if quiz:
            builder.with_quiz(quiz)
        return builder.build()


# =====================================================================
# Proxy
# =====================================================================
class ArticleAccessProxy:
    """
    Захисний замісник для Article. Має той самий набір полів для шаблону,
    але повертає повний текст і ексклюзивну галерею лише тим, кому дозволено.
    """

    PREVIEW_CHARS = 600

    def __init__(self, article: Article, user):
        self._article = article
        self._user = user

    def __getattr__(self, name):
        # усе, що не перевизначено, делегуємо реальному об'єкту
        return getattr(self._article, name)

    @property
    def user_has_premium(self) -> bool:
        if not self._user.is_authenticated:
            return False
        if self._user.is_staff:
            return True
        from accounts.models import Profile
        return Profile.for_user(self._user).is_premium

    @property
    def can_read_full(self) -> bool:
        return (not self._article.is_premium) or self.user_has_premium

    @property
    def body(self) -> str:
        if self.can_read_full:
            return self._article.body
        return self._article.body[: self.PREVIEW_CHARS].rsplit(" ", 1)[0] + "…"

    @property
    def gallery_items(self):
        qs = self._article.gallery.all()
        # ексклюзивні фото — лише передплатникам, навіть у безкоштовній статті
        if self.can_read_full and self.user_has_premium:
            return qs
        return qs.filter(is_exclusive=False)

    @property
    def hidden_exclusive_count(self) -> int:
        if self.user_has_premium:
            return 0
        return self._article.gallery.filter(is_exclusive=True).count()

    @property
    def video_url(self):
        return self._article.video_url if self.can_read_full else ""

    @property
    def real(self) -> Article:
        return self._article


# =====================================================================
# Decorator
# =====================================================================
class Renderer(ABC):
    @abstractmethod
    def render(self) -> str: ...


class ArticleRenderer(Renderer):
    """Базовий компонент: перетворює текст матеріалу на HTML."""

    def __init__(self, text: str):
        self._text = text

    def render(self) -> str:
        return linebreaks(escape(self._text))


class RendererDecorator(Renderer):
    def __init__(self, wrapped: Renderer):
        self._wrapped = wrapped

    def render(self) -> str:
        return self._wrapped.render()


class AdDecorator(RendererDecorator):
    """Вставляє рекламний блок у середину тексту (для безкоштовних читачів)."""

    def __init__(self, wrapped: Renderer, campaign):
        super().__init__(wrapped)
        self._campaign = campaign

    def render(self) -> str:
        html = super().render()
        if not self._campaign:
            return html
        c = self._campaign
        ad = (
            '<aside class="ad-block"><span class="ad-label">Реклама</span>'
            f"<strong>{escape(c.title)}</strong><p>{escape(c.text)}</p>"
            + (f'<a href="{escape(c.link)}" target="_blank" rel="noopener sponsored">Детальніше</a>' if c.link else "")
            + "</aside>"
        )
        parts = html.split("</p>")
        middle = max(1, len(parts) // 2)
        parts.insert(middle, ad)
        return "</p>".join(parts)


class PartnerBadgeDecorator(RendererDecorator):
    """Позначає рекламну інтеграцію з брендом (вимога прозорості)."""

    def __init__(self, wrapped: Renderer, partner):
        super().__init__(wrapped)
        self._partner = partner

    def render(self) -> str:
        badge = f'<div class="partner-badge">Матеріал створено у партнерстві з {escape(self._partner.name)}</div>'
        return badge + super().render()


class PaywallDecorator(RendererDecorator):
    """Додає заклик оформити підписку під обрізаним преміум-текстом."""

    def render(self) -> str:
        return super().render() + (
            '<div class="paywall"><h3>Це ексклюзив для передплатників</h3>'
            '<p>Оформіть преміум, щоб читати повністю, без реклами та з ексклюзивними фото й відео.</p>'
            '<a class="btn" href="/premium/">Оформити преміум</a></div>'
        )


def build_renderer(proxy: ArticleAccessProxy, user_sees_ads: bool, campaign=None) -> Renderer:
    """Збирає ланцюжок декораторів залежно від ситуації."""
    renderer: Renderer = ArticleRenderer(proxy.body)
    if proxy.partner:
        renderer = PartnerBadgeDecorator(renderer, proxy.partner)
    if user_sees_ads and campaign:
        renderer = AdDecorator(renderer, campaign)
    if not proxy.can_read_full:
        renderer = PaywallDecorator(renderer)
    return renderer
