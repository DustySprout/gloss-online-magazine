from django.contrib import admin

from .models import Answer, Comment, Poll, PollOption, Question, Quiz, QuizOutcome, QuizResult


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 3


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("question", "is_active", "total_votes", "created_at")
    inlines = [PollOptionInline]


class OutcomeInline(admin.StackedInline):
    model = QuizOutcome
    extra = 1


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "rubric", "is_active")
    inlines = [OutcomeInline, QuestionInline]


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 3


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "order")
    list_filter = ("quiz",)
    inlines = [AnswerInline]


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ("quiz", "user", "summary", "score", "created_at")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("article", "user", "text", "is_visible", "created_at")
    list_filter = ("is_visible",)
    list_editable = ("is_visible",)
