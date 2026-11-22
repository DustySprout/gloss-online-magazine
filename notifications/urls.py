from django.urls import path

from . import views

urlpatterns = [
    path("notifications/", views.notifications_list, name="notifications"),
    path("notifications/read/", views.mark_all_read, name="notifications_read"),
]
