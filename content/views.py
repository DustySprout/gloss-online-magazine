from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import Profile
from interactive.forms import CommentForm
from interactive.models import Poll
from monetization.services import PartnerFirstAdStrategy, active_campaigns

from .models import Article, Issue, Rubric
from .patterns import ArticleAccessProxy, build_renderer
from .recommendations import RecommendationService


def home(request):
    articles = Article.published.select_related("rubric")
    featured = articles.first()
    latest = articles[1:9]
    special = Issue.objects.filter(is_published=True, is_special=True).first()
    latest_issue = Issue.objects.filter(is_published=True).first()
    poll = Poll.objects.filter(is_active=True).first()
    recommended = RecommendationService.for_user(request.user).get(request.user, 4)
    return render(request, "content/home.html", {
        "featured": featured, "latest": latest, "special": special,
        "latest_issue": latest_issue, "poll": poll, "recommended": recommended,
    })


def rubric_view(request, slug):
    rubric = get_object_or_404(Rubric, slug=slug)
    page = Paginator(Article.published.filter(rubric=rubric), 9).get_page(request.GET.get("page"))
    return render(request, "content/rubric.html", {"rubric": rubric, "page": page})


def search(request):
    q = request.GET.get("q", "").strip()
    results = Article.published.filter(Q(title__icontains=q) | Q(lead__icontains=q)) if q else []
    return render(request, "content/search.html", {"q": q, "results": results})


def article_view(request, slug):
    article = get_object_or_404(Article.published.select_related("rubric", "partner", "author"), slug=slug)
    Article.objects.filter(pk=article.pk).update(views=F("views") + 1)

    proxy = ArticleAccessProxy(article, request.user)
    sees_ads = (not request.user.is_authenticated) or Profile.for_user(request.user).sees_ads
    campaign = PartnerFirstAdStrategy().pick(active_campaigns(), article) if sees_ads else None
    body_html = build_renderer(proxy, sees_ads, campaign).render()

    is_saved = False
    collections = []
    if request.user.is_authenticated:
        is_saved = Profile.for_user(request.user).saved_articles.filter(pk=article.pk).exists()
        collections = request.user.collections.all()

    related = Article.published.filter(rubric=article.rubric).exclude(pk=article.pk)[:3]
    return render(request, "content/article.html", {
        "article": proxy,
        "body_html": body_html,
        "comments": article.comments.filter(is_visible=True).select_related("user"),
        "comment_form": CommentForm(),
        "polls": article.polls.filter(is_active=True),
        "is_saved": is_saved,
        "collections": collections,
        "related": related,
        "share_url": request.build_absolute_uri(article.get_absolute_url()),
    })


@login_required
@require_POST
def toggle_save(request, slug):
    article = get_object_or_404(Article, slug=slug)
    profile = Profile.for_user(request.user)
    if profile.saved_articles.filter(pk=article.pk).exists():
        profile.saved_articles.remove(article)
        messages.info(request, "Прибрано зі збережених")
    else:
        profile.saved_articles.add(article)
        messages.success(request, "Збережено")
    return redirect(article.get_absolute_url())


def issues_list(request):
    issues = Issue.objects.filter(is_published=True)
    return render(request, "content/issues.html", {"issues": issues})


def issue_view(request, slug):
    issue = get_object_or_404(Issue, slug=slug, is_published=True)
    items = issue.items.select_related("article", "article__rubric")
    return render(request, "content/issue.html", {"issue": issue, "items": items})
