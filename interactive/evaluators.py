"""
GoF: Template Method — оцінювання тестів.

QuizEvaluator.evaluate() фіксує незмінний алгоритм:
    1) перевірити відповіді → 2) підрахувати → 3) сформувати результат → 4) зберегти.
Підкласи перевизначають лише кроки 2 і 3.
"""
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass

from .models import Answer, Quiz, QuizResult


@dataclass
class Evaluation:
    title: str
    description: str
    score: int | None = None
    max_score: int | None = None


class QuizEvaluator(ABC):
    def __init__(self, quiz: Quiz):
        self.quiz = quiz

    # ----- шаблонний метод -----
    def evaluate(self, user, answer_ids: list[int]) -> Evaluation:
        answers = self.validate(answer_ids)
        tally = self.tally(answers)
        result = self.build_result(tally)
        self.save(user, result)
        return result

    # ----- спільні кроки -----
    def validate(self, answer_ids):
        answers = list(Answer.objects.filter(id__in=answer_ids, question__quiz=self.quiz).select_related("question"))
        answered = {a.question_id for a in answers}
        total = self.quiz.questions.count()
        if len(answered) != total or len(answers) != total:
            raise ValueError("Потрібно відповісти на кожне питання рівно один раз")
        return answers

    def save(self, user, result: Evaluation):
        if user.is_authenticated:
            QuizResult.objects.create(quiz=self.quiz, user=user, summary=result.title, score=result.score)

    # ----- кроки, що відрізняються -----
    @abstractmethod
    def tally(self, answers): ...

    @abstractmethod
    def build_result(self, tally) -> Evaluation: ...


class PersonalityEvaluator(QuizEvaluator):
    """«Який стиль вам підходить?» — перемагає найчастіший outcome_key."""

    def tally(self, answers):
        return Counter(a.outcome_key for a in answers if a.outcome_key)

    def build_result(self, tally):
        if not tally:
            return Evaluation("Без результату", "Для цього тесту не налаштовано результати.")
        key, _ = tally.most_common(1)[0]
        outcome = self.quiz.outcomes.filter(key=key).first()
        if not outcome:
            return Evaluation(key, "")
        return Evaluation(outcome.title, outcome.description)


class ScoreEvaluator(QuizEvaluator):
    """Тест на знання — рахуємо правильні відповіді."""

    def tally(self, answers):
        return sum(1 for a in answers if a.is_correct)

    def build_result(self, tally):
        total = self.quiz.questions.count()
        ratio = tally / total if total else 0
        if ratio >= 0.8:
            verdict = "Експерт! Ви чудово знаєтеся на темі."
        elif ratio >= 0.5:
            verdict = "Непогано! Є що підтягнути."
        else:
            verdict = "Варто почитати більше наших матеріалів :)"
        return Evaluation(f"{tally} з {total}", verdict, score=tally, max_score=total)


def evaluator_for(quiz: Quiz) -> QuizEvaluator:
    if quiz.kind == Quiz.Kind.SCORE:
        return ScoreEvaluator(quiz)
    return PersonalityEvaluator(quiz)
