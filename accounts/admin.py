from django.contrib import admin

from .models import Collection, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "recommendation_mode", "premium")
    filter_horizontal = ("interests", "saved_articles")

    @admin.display(boolean=True, description="Преміум")
    def premium(self, obj):
        return obj.is_premium


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_public", "created_at")
    filter_horizontal = ("articles",)
