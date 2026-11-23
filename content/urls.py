from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("issues/", views.issues_list, name="issues"),
    path("issues/<str:slug>/", views.issue_view, name="issue"),
    path("rubric/<str:slug>/", views.rubric_view, name="rubric"),
    path("article/<str:slug>/", views.article_view, name="article"),
    path("article/<str:slug>/save/", views.toggle_save, name="toggle_save"),
    path("write/", views.write_article, name="write_article"),
    path("article/<str:slug>/edit/", views.edit_article, name="edit_article"),
    path("article/<str:slug>/delete/", views.delete_article, name="delete_article"),
]
