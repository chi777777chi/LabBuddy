import os
import reflex as rx
from ..state.auth_state import AuthState
from ..components.webview_guard import google_login_button

BACKEND_URL = os.environ.get("BACKEND_PUBLIC_URL", "http://localhost:8000")


@rx.page(route="/", on_load=[AuthState.detect_browser, AuthState.check_login_error])
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
                rx.cond(
                    AuthState.show_suspended_error,
                    rx.callout(
                        "此帳號已被停權，請聯絡管理員。",
                        icon="ban",
                        color_scheme="red",
                        variant="soft",
                        width="100%",
                    ),
                ),
                rx.divider(),
                google_login_button(BACKEND_URL),
                spacing="6",
                align="center",
                width="100%",
            ),
            width="360px",
            padding="8",
        ),
        height="100vh",
        width="100%",
        background=rx.color("gray", 2),
    )
