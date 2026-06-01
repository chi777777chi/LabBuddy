import reflex as rx


def google_login_button(backend_url: str) -> rx.Component:
    return rx.fragment(
        rx.script("""
            (function() {
                const ua = navigator.userAgent || '';
                const isWV =
                    /FBAN|FBAV|Instagram|Line\\/|MicroMessenger|WeChat|GSA/.test(ua) ||
                    (/iPhone|iPad|iPod/.test(ua) && !ua.includes('Version/')) ||
                    (/Android/.test(ua) && /wv/.test(ua));
                if (!isWV) return;

                function apply() {
                    const btn = document.getElementById('google-btn');
                    const warn = document.getElementById('webview-warn');
                    if (btn && warn) {
                        btn.style.display = 'none';
                        warn.style.display = 'flex';
                    } else {
                        setTimeout(apply, 50);
                    }
                }
                apply();
            })();
        """),
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
            id="webview-warn",
            display="none",
            flex_direction="column",
            align_items="center",
            gap="3",
            width="100%",
        ),
        rx.button(
            rx.icon("log-in", size=18),
            "使用 Google 帳號登入",
            id="google-btn",
            size="3",
            width="100%",
            on_click=rx.call_script(
                f"window.location.href='{backend_url}/auth/google'"
            ),
        ),
    )
