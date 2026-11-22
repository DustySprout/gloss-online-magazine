from django.contrib import admin, messages
from django.db.models import Max

from .models import Article, GalleryImage, Issue, IssueItem, Rubric
from .patterns import IssueDirector


@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color")
    prepopulated_fields = {"slug": ("name",)}


class GalleryInline(admin.TabularInline):
    model = GalleryImage
    extra = 1


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "rubric", "kind", "is_premium", "partner", "status", "published_at", "views")
    list_filter = ("status", "kind", "is_premium", "rubric")
    search_fields = ("title", "lead", "body")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [GalleryInline]
    actions = ["publish", "make_magazine_of_month"]

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Опублікувати вибрані")
    def publish(self, request, queryset):
        for article in queryset:  # save() по одному, щоб спрацював Observer
            article.status = Article.Status.PUBLISHED
            article.save()
        self.message_user(request, f"Опубліковано: {queryset.count()}")

    @admin.action(description="Зібрати «Журнал місяця» з найпопулярніших (Builder)")
    def make_magazine_of_month(self, request, queryset):
        number = (Issue.objects.aggregate(m=Max("number"))["m"] or 0) + 1
        try:
            issue = IssueDirector.magazine_of_the_month(number, "Найкраще за місяць")
        except ValueError as e:
            self.message_user(request, str(e), messages.ERROR)
            return
        self.message_user(request, f"Створено спецвипуск {issue}")


class IssueItemInline(admin.TabularInline):
    model = IssueItem
    extra = 1
    autocomplete_fields = ["article"]


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "month", "is_special", "is_published")
    list_filter = ("is_special", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [IssueItemInline]
