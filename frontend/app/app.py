import reflex as rx
from .pages import login, callback, home, exam_setup, exam, result, history, wrong_review, analytics, profile, admin, admin_users, admin_questions, admin_classes, admin_class_detail, teacher, teacher_class, teacher_student, teacher_stats, my_class, my_class_detail  # noqa: F401 — 匯入即註冊頁面路由

app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="blue",
        radius="medium",
    ),
    stylesheets=["custom.css"],
)
