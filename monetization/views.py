from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from accounts.models import Profile

from .models import Partner, Plan
from .services import SubscriptionFacade


def premium(request):
    current = Profile.for_user(request.user).active_subscription if request.user.is_authenticated else None
    return render(request, "monetization/premium.html", {
        "plans": Plan.objects.filter(is_active=True),
        "current": current,
        "partners": Partner.objects.all(),
    })


@login_required
@require_POST
def subscribe(request, plan_id):
    try:
        sub = SubscriptionFacade().subscribe(request.user, plan_id)
        messages.success(request, f"Підписка «{sub.plan.name}» активна до {sub.ends_at:%d.%m.%Y}")
    except (Plan.DoesNotExist, ValueError) as e:
        messages.error(request, f"Не вдалося оформити підписку: {e}")
    return redirect("premium")


@login_required
@require_POST
def cancel(request):
    SubscriptionFacade().cancel(request.user)
    messages.info(request, "Підписку скасовано")
    return redirect("premium")
