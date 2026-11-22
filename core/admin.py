from django.contrib import admin

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Singleton: новий запис створити не можна, якщо вже є
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
