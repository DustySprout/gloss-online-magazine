from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from content.models import Article

from .evaluators import evaluator_for
from .forms import CommentForm
from .models import Poll, Quiz, Vote


def polls_list(request):
    polls = Poll.objects.filter(is_active=True).prefetch_related("options")
    voted = set()
    if request.user.is_authenticated:
        voted = set(Vote.objects.filter(user=request.user).values_list("poll_id", flat=True))
    return render(request, "interactive/polls.html", {"polls": polls, "voted": voted})


@login_required
@require_POST
def vote(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id, is_active=True)
    option = poll.options.filter(pk=request.POST.get("option")).first()
    if not option:
        messages.error(request, "Оберіть варіант відповіді")
    elif Vote.objects.filter(poll=poll, user=request.user).exists():
        messages.warning(request, "Ви вже голосували в цьому опитуванні")
    else:
        Vote.objects.create(poll=poll, option=option, user=request.user)
        messages.success(request, "Дякуємо за голос!")
    return redirect(request.POST.get("next") or "polls")


def quizzes_list(request):
    return render(request, "interactive/quizzes.html", {"quizzes": Quiz.objects.filter(is_active=True)})


def quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, is_active=True)
    questions = quiz.questions.prefetch_related("answers")
    result = None
    if request.method == "POST":
        ids = [int(v) for k, v in request.POST.items() if k.startswith("q_") and v.isdigit()]
        try:
            result = evaluator_for(quiz).evaluate(request.user, ids)
        except ValueError as e:
            messages.error(request, str(e))
    return render(request, "interactive/quiz.html", {"quiz": quiz, "questions": questions, "result": result})


@login_required
@require_POST
def add_comment(request, slug):
    article = get_object_or_404(Article, slug=slug)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.article = article
        comment.user = request.user
        comment.save()
        messages.success(request, "Коментар додано")
    return redirect(article.get_absolute_url() + "#comments")
