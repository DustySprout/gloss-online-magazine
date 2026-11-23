from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from content.models import Article
from content.recommendations import RecommendationService

from .forms import CollectionForm, ProfileForm, RegisterForm
from .models import Collection, Profile


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Ласкаво просимо! Оберіть свої інтереси для рекомендацій.")
        return redirect("profile")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    prof = Profile.for_user(request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=prof)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Профіль оновлено")
        return redirect("profile")
    return render(request, "accounts/profile.html", {
        "form": form,
        "prof": prof,
        "saved": prof.saved_articles.select_related("rubric"),
        "collections": request.user.collections.all(),
        "recommended": RecommendationService.for_user(request.user).get(request.user, 6),
        "subscription": prof.active_subscription,
        "quiz_results": request.user.quiz_results.select_related("quiz")[:5],
        "collection_form": CollectionForm(),
    })


@login_required
@require_POST
def collection_create(request):
    form = CollectionForm(request.POST)
    if form.is_valid():
        c = form.save(commit=False)
        c.owner = request.user
        c.save()
        messages.success(request, f"Підбірку «{c.name}» створено")
    return redirect("profile")


def collection_view(request, pk):
    c = get_object_or_404(Collection, pk=pk)
    if not c.is_public and c.owner != request.user:
        return redirect("home")
    return render(request, "accounts/collection.html", {"collection": c, "articles": c.articles.all()})


@login_required
@require_POST
def collection_add(request, slug):
    article = get_object_or_404(Article, slug=slug)
    c = get_object_or_404(Collection, pk=request.POST.get("collection"), owner=request.user)
    c.articles.add(article)
    messages.success(request, f"Додано до підбірки «{c.name}»")
    return redirect(article.get_absolute_url())


@login_required
@require_POST
def collection_remove(request, pk, article_id):
    c = get_object_or_404(Collection, pk=pk, owner=request.user)
    c.articles.remove(article_id)
    return redirect("collection", pk=pk)


@login_required
@require_POST
def collection_delete(request, pk):
    get_object_or_404(Collection, pk=pk, owner=request.user).delete()
    messages.info(request, "Підбірку видалено")
    return redirect("profile")
