from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "GLOSS — Адмін"
admin.site.site_title = "Адмін"
admin.site.index_title = "Керування контентом"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("config.api_urls")),
    path("", include("accounts.urls")),
    path("", include("interactive.urls")),
    path("", include("monetization.urls")),
    path("", include("notifications.urls")),
    path("", include("content.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
