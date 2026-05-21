import reflex as rx
from .pages import login, callback, home, exam_setup, exam, result, history, wrong_review, analytics, profile  # noqa: F401 — 匯入即註冊頁面路由

app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="blue",
        radius="medium",
    )
)
