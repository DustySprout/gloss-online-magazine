from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("collections/new/", views.collection_create, name="collection_create"),
    path("collections/<int:pk>/", views.collection_view, name="collection"),
    path("collections/<int:pk>/delete/", views.collection_delete, name="collection_delete"),
    path("collections/<int:pk>/remove/<int:article_id>/", views.collection_remove, name="collection_remove"),
    path("article/<str:slug>/to-collection/", views.collection_add, name="collection_add"),
]
