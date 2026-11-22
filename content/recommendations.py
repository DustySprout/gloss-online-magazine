"""
GoF: Strategy — алгоритми рекомендацій статей взаємозамінні.
Контекст RecommendationService не знає, як саме добираються матеріали.
"""
from abc import ABC, abstractmethod

from django.db.models import Count

from .models import Article


class RecommendationStrategy(ABC):
    @abstractmethod
    def recommend(self, user, limit: int): ...

    @staticmethod
    def _exclude_seen(qs, user):
        if user.is_authenticated:
            qs = qs.exclude(saved_by__user=user)
        return qs


class InterestStrategy(RecommendationStrategy):
    """Матеріали з рубрик, які користувач позначив як цікаві, і схожі на збережені."""

    def recommend(self, user, limit):
        from accounts.models import Profile

        profile = Profile.for_user(user)
        rubric_ids = set(profile.interests.values_list("id", flat=True))
        rubric_ids |= set(profile.saved_articles.values_list("rubric_id", flat=True))
        if not rubric_ids:
            return PopularStrategy().recommend(user, limit)
        qs = Article.published.filter(rubric_id__in=rubric_ids)
        return list(self._exclude_seen(qs, user).order_by("-published_at")[:limit])


class PopularStrategy(RecommendationStrategy):
    """Найпопулярніше: перегляди + кількість збережень."""

    def recommend(self, user, limit):
        qs = Article.published.annotate(saves=Count("saved_by")).order_by("-views", "-saves")
        return list(self._exclude_seen(qs, user)[:limit])


class FreshStrategy(RecommendationStrategy):
    def recommend(self, user, limit):
        return list(self._exclude_seen(Article.published.all(), user)[:limit])


STRATEGIES = {
    "interests": InterestStrategy,
    "popular": PopularStrategy,
    "fresh": FreshStrategy,
}


class RecommendationService:
    def __init__(self, strategy: RecommendationStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: RecommendationStrategy):
        self._strategy = strategy

    def get(self, user, limit=6):
        return self._strategy.recommend(user, limit)

    @classmethod
    def for_user(cls, user):
        if not user.is_authenticated:
            return cls(PopularStrategy())
        from accounts.models import Profile

        mode = Profile.for_user(user).recommendation_mode
        return cls(STRATEGIES.get(mode, InterestStrategy)())
