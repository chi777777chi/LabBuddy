import os
import reflex as rx
from ..state.auth_state import AuthState

BACKEND_URL = os.environ.get("BACKEND_PUBLIC_URL", "http://localhost:8000")


@rx.page(route="/", on_load=AuthState.detect_browser)
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
                rx.cond(
                    AuthState.is_embedded_browser,
                    rx.vstack(
                        rx.callout(
                            rx.text(
                                "請用 Safari 或 Chrome 開啟此頁面",
                                weight="bold",
                            ),
                            icon="triangle_alert",
                            color_scheme="orange",
                            width="100%",
                        ),
                        rx.text(
                            "在 LINE、Instagram 等 App 內開啟連結時，Google 會拒絕登入（403 disallowed_useragent）。請複製網址後用 Safari 或 Chrome 開啟。",
                            size="2",
                            color_scheme="gray",
                            text_align="center",
                        ),
                        rx.button(
                            rx.icon("copy", size=16),
                            "複製網址",
                            size="3",
                            width="100%",
                            variant="soft",
                            color_scheme="orange",
                            on_click=rx.call_script(
                                "navigator.clipboard.writeText(window.location.href)"
                            ),
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                    ),
                    rx.button(
                        rx.icon("log-in", size=18),
                        "使用 Google 帳號登入",
                        size="3",
                        width="100%",
                        on_click=rx.call_script(
                            f"window.location.href='{BACKEND_URL}/auth/google'"
                        ),
                    ),
                ),
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
