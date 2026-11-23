"""
Генерує діаграму класів (Graphviz DOT) з позначеними GoF-патернами.
Запуск:  python build_class_diagram.py  →  class_diagram.dot
Рендер:  dot -Tpng -Gdpi=150 class_diagram.dot -o class_diagram.png
"""
from html import escape

# Кольори патернів (як у Додатку В: Фабрика — коричневий, Сінглтон — рожевий,
# Шаблонний метод — жовтий, Обсервер — зелений, Білдер — оранжевий)
P = {
    "Singleton":       ("#f8bbd0", "#ad1457"),
    "Factory Method":  ("#d7b899", "#6d4c41"),
    "Builder":         ("#ffcc80", "#e65100"),
    "Proxy":           ("#d1c4e9", "#5e35b1"),
    "Decorator":       ("#b2dfdb", "#00796b"),
    "Strategy":        ("#bbdefb", "#1565c0"),
    "Observer":        ("#c8e6c9", "#2e7d32"),
    "Template Method": ("#fff59d", "#f9a825"),
    "Facade":          ("#cfd8dc", "#455a64"),
    None:              ("#ffffff", "#555555"),
}

classes = {}   # id -> (title, stereotype, attrs, methods, pattern, abstract)
edges = []     # (from, to, kind, label)


def cls(cid, title=None, attrs=(), methods=(), pattern=None, stereo=None, abstract=False):
    classes[cid] = (title or cid, stereo, list(attrs), list(methods), pattern, abstract)


def rel(a, b, kind, label=""):
    edges.append((a, b, kind, label))


# ======================= Доменні моделі =======================
cls("User", "User (Django auth)", ["username", "email", "is_staff"])
cls("Profile", attrs=["bio", "avatar", "recommendation_mode", "email_notifications"],
    methods=["for_user(user)", "is_premium: bool", "sees_ads: bool", "active_subscription"])
cls("Collection", attrs=["name", "description", "is_public"])

cls("SingletonModel", attrs=[], methods=["save()", "delete()", "load(): SingletonModel"], pattern="Singleton", abstract=True)
cls("SiteSettings", attrs=["magazine_name", "tagline", "show_ads_to_free_users"], pattern="Singleton", stereo="singleton")

cls("Rubric", attrs=["name", "slug", "color"])
cls("Article", attrs=["title", "slug", "kind", "lead", "body", "cover", "video_url", "is_premium", "status", "views"],
    methods=["get_absolute_url()"])
cls("GalleryImage", attrs=["image", "caption", "is_exclusive"])
cls("Issue", attrs=["number", "title", "month", "is_special", "theme", "is_published"])
cls("IssueItem", attrs=["order", "section"])

cls("Poll", attrs=["question", "is_active"], methods=["results()"])
cls("PollOption", attrs=["text"])
cls("Vote", attrs=[])
cls("Quiz", attrs=["title", "kind"])
cls("Question", attrs=["text"])
cls("Answer", attrs=["text", "outcome_key", "is_correct"])
cls("QuizOutcome", attrs=["key", "title", "description"])
cls("QuizResult", attrs=["summary", "score"])
cls("Comment", attrs=["text", "is_visible"])

cls("Plan", attrs=["name", "price", "duration_days", "ad_free", "exclusive_access"])
cls("Subscription", attrs=["starts_at", "ends_at", "is_active"])
cls("Partner", attrs=["name", "website"])
cls("AdCampaign", attrs=["title", "text", "is_promo", "is_active"])
cls("Notification", attrs=["kind", "title", "message", "is_read"])

# ======================= Патерни =======================
# Factory Method
cls("ArticleCreator", methods=["create(...): Article", "configure(article) «abstract»"], pattern="Factory Method", abstract=True)
for c in ["StandardArticleCreator", "PhotoStoryCreator", "VideoStoryCreator", "InterviewCreator"]:
    cls(c, methods=["configure(article)"], pattern="Factory Method")
cls("NotificationFactory", methods=["create(event): Message"], pattern="Factory Method")

# Builder
cls("IssueBuilder", attrs=["-_items", "-_data"],
    methods=["for_month()", "as_special(theme)", "add_article(a)", "with_poll()", "with_quiz()", "published()", "build(): Issue"],
    pattern="Builder")
cls("IssueDirector", methods=["magazine_of_the_month(): Issue"], pattern="Builder", stereo="director")

# Proxy
cls("ArticleAccessProxy", attrs=["-_article: Article", "-_user"],
    methods=["can_read_full: bool", "body: str", "gallery_items", "video_url"], pattern="Proxy", stereo="proxy")

# Decorator
cls("Renderer", methods=["render(): str «abstract»"], pattern="Decorator", abstract=True)
cls("ArticleRenderer", methods=["render()"], pattern="Decorator")
cls("RendererDecorator", attrs=["-_wrapped: Renderer"], methods=["render()"], pattern="Decorator")
for c in ["AdDecorator", "PartnerBadgeDecorator", "PaywallDecorator"]:
    cls(c, methods=["render()"], pattern="Decorator")

# Strategy (рекомендації)
cls("RecommendationService", attrs=["-_strategy"], methods=["set_strategy(s)", "get(user, limit)"], pattern="Strategy", stereo="context")
cls("RecommendationStrategy", methods=["recommend(user, limit) «abstract»"], pattern="Strategy", abstract=True)
for c in ["InterestStrategy", "PopularStrategy", "FreshStrategy"]:
    cls(c, methods=["recommend()"], pattern="Strategy")
# Strategy (реклама)
cls("AdSelectionStrategy", methods=["pick(campaigns, article) «abstract»"], pattern="Strategy", abstract=True)
cls("RandomAdStrategy", methods=["pick()"], pattern="Strategy")
cls("PartnerFirstAdStrategy", methods=["pick()"], pattern="Strategy")

# Observer
cls("EventPublisher", attrs=["-_observers: list"], methods=["attach(o)", "detach(o)", "notify(event)"], pattern="Observer", stereo="subject")
cls("Observer", methods=["update(user, event, msg) «abstract»"], pattern="Observer", abstract=True)
cls("InAppObserver", methods=["update()"], pattern="Observer")
cls("EmailObserver", methods=["update()"], pattern="Observer")

# Template Method
cls("QuizEvaluator", methods=["evaluate() «template»", "validate()", "save()", "tally() «abstract»", "build_result() «abstract»"],
    pattern="Template Method", abstract=True)
cls("PersonalityEvaluator", methods=["tally()", "build_result()"], pattern="Template Method")
cls("ScoreEvaluator", methods=["tally()", "build_result()"], pattern="Template Method")

# Facade
cls("SubscriptionFacade", methods=["subscribe(user, plan_id)", "cancel(user)"], pattern="Facade", stereo="facade")
cls("PaymentGateway", methods=["charge(user, amount)"], pattern="Facade")

# ======================= Зв'язки =======================
# доменні
rel("Profile", "User", "assoc", "1  1")
rel("Profile", "Rubric", "assoc", "interests *")
rel("Profile", "Article", "assoc", "saved *")
rel("Collection", "User", "assoc", "owner")
rel("Collection", "Article", "assoc", "*")
rel("SiteSettings", "SingletonModel", "inherit")
rel("Article", "Rubric", "assoc", "*  1")
rel("Article", "Partner", "assoc", "0..1")
rel("Article", "GalleryImage", "compose", "1  *")
rel("Issue", "IssueItem", "compose", "1  *")
rel("IssueItem", "Article", "assoc")
rel("Issue", "Poll", "assoc", "featured")
rel("Issue", "Quiz", "assoc", "featured")
rel("Poll", "PollOption", "compose", "1  *")
rel("Vote", "PollOption", "assoc")
rel("Vote", "User", "assoc")
rel("Quiz", "Question", "compose", "1  *")
rel("Question", "Answer", "compose", "1  *")
rel("Quiz", "QuizOutcome", "compose", "1  *")
rel("QuizResult", "Quiz", "assoc")
rel("Comment", "Article", "assoc", "*  1")
rel("Comment", "User", "assoc")
rel("Subscription", "Plan", "assoc", "*  1")
rel("Subscription", "User", "assoc")
rel("AdCampaign", "Partner", "assoc", "*  1")
rel("Notification", "User", "assoc")

# патерни
for c in ["StandardArticleCreator", "PhotoStoryCreator", "VideoStoryCreator", "InterviewCreator"]:
    rel(c, "ArticleCreator", "inherit")
rel("ArticleCreator", "Article", "dep", "«create»")
rel("IssueDirector", "IssueBuilder", "dep", "uses")
rel("IssueBuilder", "Issue", "dep", "«create»")
rel("ArticleAccessProxy", "Article", "assoc", "wraps")
rel("ArticleRenderer", "Renderer", "inherit")
rel("RendererDecorator", "Renderer", "inherit")
rel("RendererDecorator", "Renderer", "aggr", "wraps")
for c in ["AdDecorator", "PartnerBadgeDecorator", "PaywallDecorator"]:
    rel(c, "RendererDecorator", "inherit")
rel("AdDecorator", "AdCampaign", "dep")
rel("RecommendationService", "RecommendationStrategy", "aggr")
for c in ["InterestStrategy", "PopularStrategy", "FreshStrategy"]:
    rel(c, "RecommendationStrategy", "inherit")
rel("RecommendationService", "Profile", "dep", "mode")
for c in ["RandomAdStrategy", "PartnerFirstAdStrategy"]:
    rel(c, "AdSelectionStrategy", "inherit")
rel("EventPublisher", "Observer", "aggr", "1  *")
rel("InAppObserver", "Observer", "inherit")
rel("EmailObserver", "Observer", "inherit")
rel("EventPublisher", "NotificationFactory", "dep", "uses")
rel("InAppObserver", "Notification", "dep", "«create»")
rel("PersonalityEvaluator", "QuizEvaluator", "inherit")
rel("ScoreEvaluator", "QuizEvaluator", "inherit")
rel("QuizEvaluator", "QuizResult", "dep", "«create»")
rel("SubscriptionFacade", "PaymentGateway", "dep")
rel("SubscriptionFacade", "Subscription", "dep", "«create»")
rel("SubscriptionFacade", "InAppObserver", "dep")

# ======================= Пакети (кластери) =======================
packages = [
    ("accounts", "accounts", ["User", "Profile", "Collection"]),
    ("core", "core", ["SingletonModel", "SiteSettings"]),
    ("content", "content", ["Rubric", "Article", "GalleryImage", "Issue", "IssueItem",
                            "ArticleCreator", "StandardArticleCreator", "PhotoStoryCreator", "VideoStoryCreator", "InterviewCreator",
                            "IssueBuilder", "IssueDirector", "ArticleAccessProxy",
                            "Renderer", "ArticleRenderer", "RendererDecorator", "AdDecorator", "PartnerBadgeDecorator", "PaywallDecorator",
                            "RecommendationService", "RecommendationStrategy", "InterestStrategy", "PopularStrategy", "FreshStrategy"]),
    ("interactive", "interactive", ["Poll", "PollOption", "Vote", "Quiz", "Question", "Answer", "QuizOutcome", "QuizResult", "Comment",
                                    "QuizEvaluator", "PersonalityEvaluator", "ScoreEvaluator"]),
    ("monetization", "monetization", ["Plan", "Subscription", "Partner", "AdCampaign", "SubscriptionFacade", "PaymentGateway",
                                      "AdSelectionStrategy", "RandomAdStrategy", "PartnerFirstAdStrategy"]),
    ("notifications", "notifications", ["Notification", "EventPublisher", "Observer", "InAppObserver", "EmailObserver", "NotificationFactory"]),
]


def label(cid):
    title, stereo, attrs, methods, pattern, abstract = classes[cid]
    fill, border = P[pattern]
    head = ""
    if stereo:
        head += f'<FONT POINT-SIZE="10">«{escape(stereo)}»</FONT><BR/>'
    elif abstract:
        head += '<FONT POINT-SIZE="10">«abstract»</FONT><BR/>'
    name = f"<I>{escape(title)}</I>" if abstract else escape(title)
    head += f"<B>{name}</B>"
    rows = [f'<TR><TD BGCOLOR="{fill}" COLOR="{border}">{head}</TD></TR>']
    a = "<BR ALIGN=\"LEFT\"/>".join(escape(x) for x in attrs) + ('<BR ALIGN="LEFT"/>' if attrs else "")
    m = "<BR ALIGN=\"LEFT\"/>".join(escape(x) for x in methods) + ('<BR ALIGN="LEFT"/>' if methods else "")
    rows.append(f'<TR><TD ALIGN="LEFT" BALIGN="LEFT" COLOR="{border}">{a or " "}</TD></TR>')
    if methods:
        rows.append(f'<TR><TD ALIGN="LEFT" BALIGN="LEFT" COLOR="{border}">{m}</TD></TR>')
    return f'<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" COLOR="{border}" BGCOLOR="white">{"".join(rows)}</TABLE>>'


EDGE = {
    "inherit": 'arrowhead=onormal, arrowsize=1.1, color="#333333"',
    "assoc":   'arrowhead=vee, arrowsize=0.7, color="#777777"',
    "compose": 'dir=back, arrowtail=diamond, arrowhead=none, color="#555555"',
    "aggr":    'dir=back, arrowtail=odiamond, arrowhead=none, color="#555555"',
    "dep":     'arrowhead=vee, style=dashed, arrowsize=0.7, color="#888888"',
}


def build():
    out = [
        "// Згенеровано build_class_diagram.py",
        "digraph Classes {",
        '  graph [rankdir=BT, fontname="DejaVu Sans", fontsize=26, labelloc=t, '
        'label="Діаграма класів: онлайн-журнал GLOSS (GoF-патерни позначено кольорами)\\n ", '
        "nodesep=0.35, ranksep=0.7, pad=0.5, newrank=true, splines=true];",
        '  node [shape=plain, fontname="DejaVu Sans", fontsize=11];',
        '  edge [fontname="DejaVu Sans", fontsize=9, fontcolor="#555555"];',
    ]
    for pid, plabel, members in packages:
        out.append(f'  subgraph cluster_{pid} {{ label="package {plabel}"; fontsize=15; style="rounded,dashed"; color="#9e9e9e"; margin=14;')
        for m in members:
            out.append(f"    {m} [label={label(m)}];")
        out.append("  }")
    for a, b, kind, lab in edges:
        compose_like = kind in ("compose", "aggr")
        src, dst = (b, a) if compose_like else (a, b)  # для композиції ромб біля «цілого»
        extra = f', label="{lab}"' if lab else ""
        if compose_like:
            out.append(f"  {dst} -> {src} [{EDGE[kind]}{extra}];")
        else:
            out.append(f"  {src} -> {dst} [{EDGE[kind]}{extra}];")
    # легенда
    rows = "".join(
        f'<TR><TD BGCOLOR="{f}" COLOR="{b}" WIDTH="26"> </TD><TD ALIGN="LEFT">{escape(name)}</TD></TR>'
        for name, (f, b) in P.items() if name
    )
    out.append(
        '  legend [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="3" CELLPADDING="3" COLOR="#9e9e9e">'
        f'<TR><TD COLSPAN="2"><B>GoF-патерни</B></TD></TR>{rows}'
        '<TR><TD BGCOLOR="white" COLOR="#555555" BORDER="1"> </TD><TD ALIGN="LEFT">доменна модель (Django ORM)</TD></TR>'
        "</TABLE>>];"
    )
    out.append("}")
    return "\n".join(out)


if __name__ == "__main__":
    from pathlib import Path
    Path(__file__).with_name("class_diagram.dot").write_text(build(), encoding="utf-8")
    print("class_diagram.dot збережено")
