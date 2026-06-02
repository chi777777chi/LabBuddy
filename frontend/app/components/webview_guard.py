import reflex as rx
from ..state.auth_state import AuthState


def google_login_button(backend_url: str) -> rx.Component:
    return rx.cond(
        AuthState.is_embedded_browser,
        # WebView 警告 UI
        rx.box(
            rx.callout(
                rx.text("請用 Safari 或 Chrome 開啟此頁面才能登入", weight="bold"),
                icon="triangle_alert",
                color_scheme="orange",
                width="100%",
            ),
            rx.text(
                "在 LINE、Instagram 等 App 內開啟連結時，Google 會拒絕登入。",
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
            display="flex",
            flex_direction="column",
            align_items="center",
            gap="3",
            width="100%",
        ),
        # 一般瀏覽器登入按鈕
        rx.button(
            rx.icon("log-in", size=18),
            "使用 Google 帳號登入",
            size="3",
            width="100%",
            on_click=rx.call_script(
                f"window.location.href='{backend_url}/auth/google'"
            ),
        ),
    )
