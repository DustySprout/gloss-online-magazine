from django.urls import path

from . import views

urlpatterns = [
    path("premium/", views.premium, name="premium"),
    path("premium/subscribe/<int:plan_id>/", views.subscribe, name="subscribe"),
    path("premium/cancel/", views.cancel, name="cancel_subscription"),
]
