import reflex as rx
from ..state.auth_state import AuthState


def nav_bar() -> rx.Component:
    return rx.hstack(
        rx.heading("醫檢師國考練習平台", size="4"),
        rx.spacer(),
        rx.hstack(
            rx.avatar(src=AuthState.user_avatar, fallback=AuthState.user_name, size="2"),
            rx.text(AuthState.user_name, weight="medium"),
            rx.button(
                rx.icon("log-out", size=16),
                "登出",
                on_click=AuthState.logout,
                size="2",
                variant="ghost",
                color_scheme="gray",
            ),
            align="center",
            spacing="3",
        ),
        width="100%",
        padding_x="6",
        padding_y="4",
        border_bottom=f"1px solid {rx.color('gray', 4)}",
        background="white",
    )


def menu_card(icon: str, title: str, description: str, route: str) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon(icon, size=36, color=rx.color("blue", 9)),
            rx.heading(title, size="4"),
            rx.text(description, color_scheme="gray", text_align="center", size="2"),
            align="center",
            spacing="3",
            padding="4",
        ),
        on_click=rx.redirect(route),
        cursor="pointer",
        _hover={"box_shadow": "0 4px 16px rgba(0,0,0,0.10)"},
        transition="box-shadow 0.2s",
        width="200px",
    )


@rx.page(route="/home", on_load=AuthState.load_user)
def home_page() -> rx.Component:
    return rx.box(
        nav_bar(),
        rx.center(
            rx.vstack(
                rx.text(
                    "歡迎回來，",
                    rx.text.span(AuthState.user_name, weight="bold"),
                    size="4",
                    padding_top="8",
                ),
                rx.hstack(
                    menu_card("pencil", "開始測驗", "選擇科目與模式，開始練習", "/exam-setup"),
                    menu_card("clock", "歷史紀錄", "查看過去的測驗成績與詳解", "/history"),
                    menu_card("bookmark-x", "錯題複習", "針對答錯的題目加強練習", "/wrong-review"),
                    menu_card("user", "個人資料", "管理帳號與學習統計", "/profile"),
                    spacing="6",
                    flex_wrap="wrap",
                    justify="center",
                ),
                spacing="8",
                align="center",
            ),
            padding="8",
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
