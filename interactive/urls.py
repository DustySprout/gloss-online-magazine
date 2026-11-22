from django.urls import path

from . import views

urlpatterns = [
    path("polls/", views.polls_list, name="polls"),
    path("polls/<int:poll_id>/vote/", views.vote, name="vote"),
    path("quizzes/", views.quizzes_list, name="quizzes"),
    path("quizzes/<int:quiz_id>/", views.quiz_view, name="quiz"),
    path("article/<str:slug>/comment/", views.add_comment, name="add_comment"),
]
