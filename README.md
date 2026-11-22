# GLOSS — тематичний онлайн-журнал

Курсова робота з дисципліни «Документування програмного забезпечення та шаблони проектування», варіант 15.

Веб-додаток імітує роботу глянцевого онлайн-журналу: рубрики, статті з фото та відео, випуски та спецвипуск «Журнал місяця», опитування, тести, коментарі, поширення в соцмережах, профіль із збереженими матеріалами, підбірками й рекомендаціями, преміум-підписка, реклама партнерів і сповіщення.

## Технології

| Шар | Технології |
|---|---|
| Бекенд | Python 3.12+, Django 5, Django REST Framework |
| База даних | MySQL 8+ (драйвер PyMySQL) |
| Фронтенд | Шаблони Django, HTML5, CSS3 (адаптивна верстка) |
| Адмін-частина | Django Admin (українська локалізація) |
| Тестування API | Браузерний інтерфейс DRF, Postman |

## Структура

```
config/          налаштування, головні URL, роутер REST API
core/            SiteSettings (Singleton), контекст для шаблонів
accounts/        профіль, інтереси, збережене, підбірки, реєстрація
content/         рубрики, матеріали, галерея, випуски; патерни контенту; рекомендації
interactive/     опитування, тести, коментарі; оцінювання тестів
monetization/    тарифи, підписки, партнери, реклама; фасад підписки
notifications/   сповіщення та їх розсилка (Observer)
templates/       HTML-шаблони
static/css/      стилі
```

## GoF-патерни

| Патерн | Де | Навіщо |
|---|---|---|
| **Singleton** | `core/models.py` → `SingletonModel`, `SiteSettings` | Глобальні налаштування журналу існують в одному екземплярі |
| **Factory Method** | `content/patterns.py` → `ArticleCreator` і підкласи (`StandardArticleCreator`, `PhotoStoryCreator`, `VideoStoryCreator`, `InterviewCreator`) | Створення матеріалів різних типів з власними правилами (відео потребує посилання, інтерв'ю — імені гостя) |
| **Factory Method** | `notifications/observer.py` → `NotificationFactory` | Формування тексту сповіщення залежно від типу події |
| **Builder** | `content/patterns.py` → `IssueBuilder`, `IssueDirector` | Покрокове збирання випуску та спецвипуску «Журнал місяця» |
| **Proxy** | `content/patterns.py` → `ArticleAccessProxy` | Контроль доступу до преміум-тексту, ексклюзивних фото й відео |
| **Decorator** | `content/patterns.py` → `ArticleRenderer`, `AdDecorator`, `PartnerBadgeDecorator`, `PaywallDecorator` | Динамічно додає до статті рекламу, позначку партнера і paywall |
| **Strategy** | `content/recommendations.py` → `InterestStrategy`, `PopularStrategy`, `FreshStrategy` | Взаємозамінні алгоритми рекомендацій (користувач обирає режим у профілі) |
| **Strategy** | `monetization/services.py` → `RandomAdStrategy`, `PartnerFirstAdStrategy` | Вибір рекламного блоку для показу |
| **Observer** | `notifications/observer.py` → `EventPublisher`, `InAppObserver`, `EmailObserver`; `notifications/signals.py` | Сповіщення про новий випуск, ексклюзив для передплатників, акції партнерів |
| **Template Method** | `interactive/evaluators.py` → `QuizEvaluator`, `PersonalityEvaluator`, `ScoreEvaluator` | Спільний алгоритм оцінювання тесту з різними кроками підрахунку |
| **Facade** | `monetization/services.py` → `SubscriptionFacade` | Один метод `subscribe()` приховує перевірку тарифу, оплату, продовження та сповіщення |

## Запуск (Windows)

### 1. Встановіть

- Python 3.12 або новіший (під час встановлення поставте галочку **Add python.exe to PATH**)
- MySQL Server і MySQL Workbench
- Git (або GitHub Desktop)

### 2. Створіть базу даних

У MySQL Workbench відкрийте Local instance і виконайте:

```sql
CREATE DATABASE magazine_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Налаштуйте проєкт

У терміналі (PowerShell) в папці проєкту:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Відкрийте файл `.env` і впишіть свій пароль MySQL у `DB_PASSWORD`.

### 4. Створіть таблиці, адміністратора й демо-дані

```powershell
python manage.py makemigrations core accounts content interactive monetization notifications
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
```

Демо-фото лежать у папці `demo_media/` (вона є в репозиторії) і копіюються в `media/` під час `seed_demo`.
Щоб перестворити демо-контент з нуля: `python manage.py seed_demo --reset`.

### 5. Запустіть сервер

```powershell
python manage.py runserver
```

- Сайт: http://127.0.0.1:8000/
- Адмінка: http://127.0.0.1:8000/admin/
- REST API: http://127.0.0.1:8000/api/

## REST API

| Метод | Адреса | Опис |
|---|---|---|
| GET | `/api/rubrics/` | Рубрики |
| GET/POST | `/api/articles/` | Список матеріалів (`?rubric=<slug>`), створення через Factory Method (staff) |
| GET | `/api/articles/<slug>/` | Матеріал (текст обрізається для преміум без підписки) |
| POST | `/api/articles/<slug>/save/` | Зберегти / прибрати зі збережених |
| GET | `/api/articles/recommended/` | Рекомендації (Strategy) |
| GET | `/api/issues/` | Випуски з матеріалами |
| GET | `/api/polls/`, POST `/api/polls/<id>/vote/` | Опитування, голосування `{"option": id}` |
| GET | `/api/quizzes/`, POST `/api/quizzes/<id>/submit/` | Тести, відповіді `{"answers": [id, ...]}` |
| GET/POST | `/api/comments/?article=<id>` | Коментарі |
| GET/POST | `/api/collections/` | Власні підбірки |
| GET | `/api/plans/`, POST `/api/plans/<id>/subscribe/` | Тарифи, оформлення підписки (Facade) |
| GET | `/api/notifications/`, POST `/api/notifications/read_all/` | Сповіщення |
| GET | `/api/me/` | Поточний користувач |

Авторизація: сесія (після входу на сайті) або Basic Auth у Postman.

## Як перевірити основні сценарії

1. Зареєструйтеся, оберіть інтереси в профілі — з'являться рекомендації.
2. Відкрийте преміум-статтю без підписки — побачите обрізаний текст і заклик (Proxy + Decorator).
3. Оформіть підписку на `/premium/` — реклама зникне, текст відкриється повністю.
4. В адмінці опублікуйте новий випуск або створіть акцію партнера з галочкою «Акція» — користувачі отримають сповіщення (Observer).
5. В адмінці «Матеріали» виберіть будь-які записи → дія «Зібрати «Журнал місяця»» (Builder).
6. Пройдіть тест «Який стиль вам підходить?» (Template Method).

Оплата в проєкті імітується: реальні кошти не списуються. Листи-сповіщення в режимі розробки друкуються в консоль сервера.
