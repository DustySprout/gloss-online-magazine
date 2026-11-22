"""REST API: усі ресурси під префіксом /api/ (DRF-роутер дає HTML-перегляд у браузері)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.api import CollectionViewSet, me
from content.api import ArticleViewSet, IssueViewSet, RubricViewSet
from interactive.api import CommentViewSet, PollViewSet, QuizViewSet
from monetization.api import PartnerViewSet, PlanViewSet
from notifications.api import NotificationViewSet

router = DefaultRouter()
router.register("rubrics", RubricViewSet)
router.register("articles", ArticleViewSet, basename="article")
router.register("issues", IssueViewSet, basename="issue")
router.register("polls", PollViewSet)
router.register("quizzes", QuizViewSet)
router.register("comments", CommentViewSet, basename="comment")
router.register("collections", CollectionViewSet, basename="collection")
router.register("plans", PlanViewSet)
router.register("partners", PartnerViewSet)
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("me/", me, name="api-me"),
    path("auth/", include("rest_framework.urls")),
    path("", include(router.urls)),
]
