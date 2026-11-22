from django.db.utils import DatabaseError

from .models import SiteSettings


def site_context(request):
    """Додає в кожен шаблон налаштування журналу, рубрики і лічильник сповіщень."""
    from content.models import Rubric

    try:
        settings_obj = SiteSettings.load()
        rubrics = list(Rubric.objects.all())
    except DatabaseError:  # до першої міграції таблиць ще немає
        return {}

    from accounts.models import Profile

    unread = 0
    is_premium = False
    if request.user.is_authenticated:
        unread = request.user.notifications.filter(is_read=False).count()
        is_premium = Profile.for_user(request.user).is_premium
    return {
        "site": settings_obj,
        "nav_rubrics": rubrics,
        "unread_count": unread,
        "is_premium": is_premium,
    }
