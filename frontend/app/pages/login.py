import os
import reflex as rx
from ..components.webview_guard import WebViewGuard

BACKEND_URL = os.environ.get("BACKEND_PUBLIC_URL", "http://localhost:8000")


@rx.page(route="/")
def login_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.vstack(
                    rx.heading("醫檢師國考練習平台", size="7", text_align="center"),
                    rx.text(
                        "台灣醫事檢驗師國家考試線上題庫",
                        color_scheme="gray",
                        text_align="center",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.divider(),
                WebViewGuard.create(backend_url=BACKEND_URL),
                spacing="6",
                align="center",
                width="100%",
            ),
            width="360px",
            padding="8",
        ),
        height="100vh",
        background=rx.color("gray", 2),
    )
