"""
Наповнює БД демонстраційними даними.

    python manage.py seed_demo           — якщо база порожня
    python manage.py seed_demo --reset   — видалити старий демо-контент і створити заново
"""
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max

from content import demo_content as D
from content.models import Article, GalleryImage, Issue, Rubric
from content.patterns import IssueBuilder, IssueDirector, get_creator
from interactive.models import Answer, Comment, Poll, PollOption, Question, Quiz, QuizOutcome
from monetization.models import AdCampaign, Partner, Plan, Subscription
from notifications.models import Notification

MEDIA_SRC = Path(settings.BASE_DIR) / "demo_media"


def attach(field, filename):
    path = MEDIA_SRC / filename
    if path.exists():
        with path.open("rb") as f:
            field.save(filename, File(f), save=False)


class Command(BaseCommand):
    help = "Створює демонстраційні рубрики, матеріали з фото, опитування, тест, тарифи та випуски"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Видалити наявний контент і створити заново")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["reset"]:
            self.reset()
        elif Article.objects.exists():
            self.stdout.write(self.style.WARNING("Дані вже є. Щоб оновити, запустіть: python manage.py seed_demo --reset"))
            return

        author = User.objects.filter(is_superuser=True).first()
        rubrics = {}
        for name, color, desc in D.RUBRICS:
            rubrics[name], _ = Rubric.objects.get_or_create(name=name, defaults={"color": color, "description": desc})

        partner = Partner.objects.create(
            name="UrbanStep", website="https://example.com",
            description="Український бренд взуття для міста й подорожей.",
        )
        Plan.objects.create(name="Преміум місяць", price=99, duration_days=30, description="Скасування будь-коли")
        Plan.objects.create(name="Преміум рік", price=890, duration_days=365, description="Два місяці в подарунок")
        Plan.objects.create(name="Без реклами", price=49, duration_days=30, exclusive_access=False,
                            description="Лише прибирає рекламу")
        AdCampaign.objects.create(partner=partner, title="Зимова колекція UrbanStep",
                                  text="Знижка 20% за промокодом GLOSS.", link="https://example.com")

        articles = []
        for kind, rubric, title, lead, body, premium, cover, gallery, extra in D.ARTICLES:
            extra = dict(extra)
            with_partner = extra.pop("partner", False)
            a = get_creator(kind).create(  # Factory Method
                title=title, rubric=rubrics[rubric], author=author,
                lead=lead, body=body, is_premium=premium, **extra,
            )
            attach(a.cover, cover)
            if with_partner:
                a.partner = partner
            a.save()
            for order, (img, caption, exclusive) in enumerate(gallery):
                g = GalleryImage(article=a, caption=caption, is_exclusive=exclusive, order=order)
                attach(g.image, img)
                if g.image:
                    g.save()
            articles.append(a)

        for i, a in enumerate(articles):
            a.status = Article.Status.PUBLISHED
            a.views = (len(articles) - i) * 37
            a.save()

        polls = []
        for question, rubric, options in D.POLLS:
            article = next((a for a in articles if a.rubric.name == rubric), None)
            poll = Poll.objects.create(question=question, article=article)
            for t in options:
                PollOption.objects.create(poll=poll, text=t)
            polls.append(poll)

        q = D.QUIZ
        quiz = Quiz.objects.create(title=q["title"], description=q["description"], rubric=rubrics[q["rubric"]])
        keys = list(q["outcomes"])
        for key, (t, desc) in q["outcomes"].items():
            QuizOutcome.objects.create(quiz=quiz, key=key, title=t, description=desc)
        for order, (text, answers) in enumerate(q["questions"]):
            question = Question.objects.create(quiz=quiz, text=text, order=order)
            for answer, key in zip(answers, keys):
                Answer.objects.create(question=question, text=answer, outcome_key=key)

        reader, created = User.objects.get_or_create(username="olena_reader", defaults={"first_name": "Олена"})
        if created:
            reader.set_unusable_password()
            reader.save()
        for idx, text in D.COMMENTS:
            Comment.objects.create(article=articles[idx], user=reader, text=text)

        # Builder: звичайний випуск
        number = (Issue.objects.aggregate(m=Max("number"))["m"] or 0) + 1
        (IssueBuilder(number, "Зима вдома і в горах")
            .with_editor_note("Гори, Львів, нова GTA і поради, як отримати роботу мрії.")
            .add_articles(articles[:3], "Головне")
            .add_articles(articles[3:6], "Також у номері")
            .with_poll(polls[0])
            .published()
            .build())
        # Builder + Director: «Журнал місяця»
        IssueDirector.magazine_of_the_month(number + 1, "Найкраще за місяць", poll=polls[1], quiz=quiz)

        self.stdout.write(self.style.SUCCESS("Демо-дані створено."))

    def reset(self):
        Notification.objects.all().delete()
        Subscription.objects.all().delete()
        Issue.objects.all().delete()
        Poll.objects.all().delete()
        Quiz.objects.all().delete()
        Comment.objects.all().delete()
        Article.objects.all().delete()
        AdCampaign.objects.all().delete()
        Partner.objects.all().delete()
        Plan.objects.all().delete()
        Rubric.objects.all().delete()
        self.stdout.write("Старий контент видалено.")
