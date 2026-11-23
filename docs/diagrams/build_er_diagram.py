"""
ER-діаграма бази даних magazine_db (MySQL) у Graphviz.
Запуск: python build_er_diagram.py && dot -Tpng -Gdpi=150 er_diagram.dot -o er_diagram.png
"""
from html import escape
from pathlib import Path

# таблиця -> [(колонка, тип, ключ)]  ключ: PK / FK / UQ / ""
T = {
    "auth_user": [("id", "int", "PK"), ("username", "varchar(150)", "UQ"), ("email", "varchar(254)", ""), ("password", "varchar(128)", ""), ("is_staff", "bool", "")],
    "accounts_profile": [("id", "bigint", "PK"), ("user_id", "int", "FK UQ"), ("bio", "varchar(300)", ""), ("avatar", "varchar(100)", ""), ("recommendation_mode", "varchar(20)", ""), ("email_notifications", "bool", "")],
    "accounts_profile_interests": [("id", "bigint", "PK"), ("profile_id", "bigint", "FK"), ("rubric_id", "bigint", "FK")],
    "accounts_profile_saved_articles": [("id", "bigint", "PK"), ("profile_id", "bigint", "FK"), ("article_id", "bigint", "FK")],
    "accounts_collection": [("id", "bigint", "PK"), ("owner_id", "int", "FK"), ("name", "varchar(120)", ""), ("is_public", "bool", "")],
    "accounts_collection_articles": [("id", "bigint", "PK"), ("collection_id", "bigint", "FK"), ("article_id", "bigint", "FK")],
    "core_sitesettings": [("id", "bigint", "PK = 1"), ("magazine_name", "varchar(100)", ""), ("tagline", "varchar(200)", ""), ("show_ads_to_free_users", "bool", "")],
    "content_rubric": [("id", "bigint", "PK"), ("name", "varchar(80)", "UQ"), ("slug", "varchar(100)", "UQ"), ("color", "varchar(7)", "")],
    "content_article": [("id", "bigint", "PK"), ("rubric_id", "bigint", "FK"), ("author_id", "int", "FK"), ("partner_id", "bigint", "FK"), ("title", "varchar(200)", ""), ("slug", "varchar(220)", "UQ"), ("kind", "varchar(20)", ""), ("body", "longtext", ""), ("cover", "varchar(100)", ""), ("is_premium", "bool", ""), ("status", "varchar(20)", ""), ("published_at", "datetime", ""), ("views", "int unsigned", "")],
    "content_galleryimage": [("id", "bigint", "PK"), ("article_id", "bigint", "FK"), ("image", "varchar(100)", ""), ("is_exclusive", "bool", "")],
    "content_issue": [("id", "bigint", "PK"), ("number", "int unsigned", "UQ"), ("title", "varchar(200)", ""), ("is_special", "bool", ""), ("is_published", "bool", ""), ("featured_poll_id", "bigint", "FK"), ("featured_quiz_id", "bigint", "FK")],
    "content_issueitem": [("id", "bigint", "PK"), ("issue_id", "bigint", "FK"), ("article_id", "bigint", "FK"), ("order", "int unsigned", ""), ("section", "varchar(80)", "")],
    "interactive_poll": [("id", "bigint", "PK"), ("article_id", "bigint", "FK"), ("question", "varchar(250)", ""), ("is_active", "bool", "")],
    "interactive_polloption": [("id", "bigint", "PK"), ("poll_id", "bigint", "FK"), ("text", "varchar(150)", "")],
    "interactive_vote": [("id", "bigint", "PK"), ("poll_id", "bigint", "FK"), ("option_id", "bigint", "FK"), ("user_id", "int", "FK"), ("UNIQUE(poll_id, user_id)", "", "")],
    "interactive_quiz": [("id", "bigint", "PK"), ("title", "varchar(200)", ""), ("kind", "varchar(20)", ""), ("rubric_id", "bigint", "FK")],
    "interactive_question": [("id", "bigint", "PK"), ("quiz_id", "bigint", "FK"), ("text", "varchar(250)", "")],
    "interactive_answer": [("id", "bigint", "PK"), ("question_id", "bigint", "FK"), ("text", "varchar(200)", ""), ("outcome_key", "varchar(30)", ""), ("is_correct", "bool", "")],
    "interactive_quizoutcome": [("id", "bigint", "PK"), ("quiz_id", "bigint", "FK"), ("key", "varchar(30)", ""), ("title", "varchar(120)", "")],
    "interactive_quizresult": [("id", "bigint", "PK"), ("quiz_id", "bigint", "FK"), ("user_id", "int", "FK"), ("summary", "varchar(200)", ""), ("score", "int unsigned", "")],
    "interactive_comment": [("id", "bigint", "PK"), ("article_id", "bigint", "FK"), ("user_id", "int", "FK"), ("text", "longtext", ""), ("is_visible", "bool", "")],
    "monetization_plan": [("id", "bigint", "PK"), ("name", "varchar(80)", ""), ("price", "decimal(8,2)", ""), ("duration_days", "int unsigned", ""), ("ad_free", "bool", ""), ("exclusive_access", "bool", "")],
    "monetization_subscription": [("id", "bigint", "PK"), ("user_id", "int", "FK"), ("plan_id", "bigint", "FK"), ("starts_at", "datetime", ""), ("ends_at", "datetime", ""), ("is_active", "bool", "")],
    "monetization_partner": [("id", "bigint", "PK"), ("name", "varchar(120)", ""), ("website", "varchar(200)", "")],
    "monetization_adcampaign": [("id", "bigint", "PK"), ("partner_id", "bigint", "FK"), ("title", "varchar(150)", ""), ("is_promo", "bool", ""), ("is_active", "bool", "")],
    "notifications_notification": [("id", "bigint", "PK"), ("user_id", "int", "FK"), ("kind", "varchar(20)", ""), ("title", "varchar(200)", ""), ("is_read", "bool", "")],
}

# (дочірня, колонка, батьківська, підпис)  — зв'язок N:1 від FK до PK
R = [
    ("accounts_profile", "user_id", "auth_user", "1:1"),
    ("accounts_profile_interests", "profile_id", "accounts_profile", ""), ("accounts_profile_interests", "rubric_id", "content_rubric", ""),
    ("accounts_profile_saved_articles", "profile_id", "accounts_profile", ""), ("accounts_profile_saved_articles", "article_id", "content_article", ""),
    ("accounts_collection", "owner_id", "auth_user", ""),
    ("accounts_collection_articles", "collection_id", "accounts_collection", ""), ("accounts_collection_articles", "article_id", "content_article", ""),
    ("content_article", "rubric_id", "content_rubric", ""), ("content_article", "author_id", "auth_user", ""), ("content_article", "partner_id", "monetization_partner", ""),
    ("content_galleryimage", "article_id", "content_article", ""),
    ("content_issueitem", "issue_id", "content_issue", ""), ("content_issueitem", "article_id", "content_article", ""),
    ("content_issue", "featured_poll_id", "interactive_poll", ""), ("content_issue", "featured_quiz_id", "interactive_quiz", ""),
    ("interactive_poll", "article_id", "content_article", ""),
    ("interactive_polloption", "poll_id", "interactive_poll", ""),
    ("interactive_vote", "poll_id", "interactive_poll", ""), ("interactive_vote", "option_id", "interactive_polloption", ""), ("interactive_vote", "user_id", "auth_user", ""),
    ("interactive_quiz", "rubric_id", "content_rubric", ""),
    ("interactive_question", "quiz_id", "interactive_quiz", ""), ("interactive_answer", "question_id", "interactive_question", ""),
    ("interactive_quizoutcome", "quiz_id", "interactive_quiz", ""), ("interactive_quizresult", "quiz_id", "interactive_quiz", ""), ("interactive_quizresult", "user_id", "auth_user", ""),
    ("interactive_comment", "article_id", "content_article", ""), ("interactive_comment", "user_id", "auth_user", ""),
    ("monetization_subscription", "user_id", "auth_user", ""), ("monetization_subscription", "plan_id", "monetization_plan", ""),
    ("monetization_adcampaign", "partner_id", "monetization_partner", ""),
    ("notifications_notification", "user_id", "auth_user", ""),
]

APPS = {
    "auth": ("Django auth", "#eceff1"), "accounts": ("accounts", "#fce4ec"), "core": ("core", "#f3e5f5"),
    "content": ("content", "#e3f2fd"), "interactive": ("interactive", "#e8f5e9"),
    "monetization": ("monetization", "#fff3e0"), "notifications": ("notifications", "#f1f8e9"),
}


def node(name, cols):
    app = name.split("_")[0]
    color = APPS[app][1]
    rows = [f'<TR><TD COLSPAN="3" BGCOLOR="{color}"><B>{escape(name)}</B></TD></TR>']
    for col, typ, key in cols:
        k = f'<FONT COLOR="#c2185b"><B>{escape(key)}</B></FONT>' if key else " "
        c = f"<U>{escape(col)}</U>" if key.startswith("PK") else escape(col)
        tcell = f'<TD ALIGN="LEFT"><FONT COLOR="#666666">{escape(typ)}</FONT></TD>' if typ else "<TD> </TD>"
        port = escape(col.split("(")[0])
        rows.append(f'<TR><TD PORT="{port}" ALIGN="LEFT">{c}</TD>{tcell}<TD ALIGN="LEFT">{k}</TD></TR>')
    return f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#90a4ae">{"".join(rows)}</TABLE>>'


def build():
    out = ['digraph ER {',
           '  graph [rankdir=LR, fontname="DejaVu Sans", fontsize=24, labelloc=t, nodesep=0.3, ranksep=1.1, pad=0.4,',
           '         label="ER-діаграма бази даних magazine_db (MySQL, InnoDB, utf8mb4)\\n "];',
           '  node [shape=plain, fontname="DejaVu Sans", fontsize=10];',
           '  edge [color="#78909c", arrowhead=teetee, arrowtail=crowodot, dir=both, fontname="DejaVu Sans", fontsize=9];']
    for app, (label, color) in APPS.items():
        out.append(f'  subgraph cluster_{app} {{ label="{label}"; fontsize=14; style="rounded,dashed"; color="#b0bec5";')
        for name, cols in T.items():
            if name.split("_")[0] == app:
                out.append(f"    {name} [label={node(name, cols)}];")
        out.append("  }")
    for child, col, parent, lab in R:
        extra = f' [label="{lab}", arrowtail=teetee]' if lab == "1:1" else ""
        out.append(f'  {child}:{col} -> {parent}:id{extra};')
    out.append("}")
    return "\n".join(out)


if __name__ == "__main__":
    Path(__file__).with_name("er_diagram.dot").write_text(build(), encoding="utf-8")
    print("er_diagram.dot збережено")
