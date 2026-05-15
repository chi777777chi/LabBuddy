import reflex as rx
from .pages import login, callback, home, exam_setup, exam, result  # noqa: F401 — 匯入即註冊頁面路由

app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="blue",
        radius="medium",
    )
)
