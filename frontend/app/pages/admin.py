import reflex as rx
from ..state.auth_state import AuthState
from ..state.admin_state import AdminState


def admin_nav_bar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.icon("shield", size=18, color=rx.color("red", 9)),
            rx.heading(
                "管理員後台",
                size="4",
                on_click=rx.call_script("window.location.href='/admin'"),
                cursor="pointer",
            ),
            spacing="2",
            align="center",
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(
                rx.icon("layout-dashboard", size=15),
                "總覽",
                on_click=rx.call_script("window.location.href='/admin'"),
                size="2",
                variant="ghost",
                color_scheme="gray",
            ),
            rx.button(
                rx.icon("users", size=15),
                "使用者",
                on_click=rx.call_script("window.location.href='/admin/users'"),
                size="2",
                variant="ghost",
                color_scheme="gray",
            ),
            rx.button(
                rx.icon("book-open", size=15),
                "題庫",
                on_click=rx.call_script("window.location.href='/admin/questions'"),
                size="2",
                variant="ghost",
                color_scheme="gray",
            ),
            rx.button(
                rx.icon("house", size=15),
                "回主選單",
                on_click=rx.call_script("window.location.href='/home'"),
                size="2",
                variant="ghost",
                color_scheme="blue",
            ),
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


def stat_card(label: str, value, icon: str, color: str) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=20, color=rx.color(color, 9)),
                rx.text(label, size="2", color=rx.color("gray", 10), weight="medium"),
                spacing="2",
                align="center",
            ),
            rx.heading(value, size="7", color=rx.color(color, 10)),
            spacing="2",
            align="start",
        ),
        padding="4",
        width="100%",
    )


def subject_count_row(item: dict) -> rx.Component:
    return rx.hstack(
        rx.text(item["subject"], weight="medium", size="2"),
        rx.spacer(),
        rx.badge(item["count"], " 題", color_scheme="blue", variant="soft"),
        width="100%",
        padding_y="2",
        border_bottom=f"1px solid {rx.color('gray', 4)}",
    )


def nav_card(icon: str, title: str, description: str, route: str, color: str) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon(icon, size=36, color=rx.color(color, 9)),
            rx.heading(title, size="4"),
            rx.text(description, color_scheme="gray", text_align="center", size="2"),
            align="center",
            spacing="3",
            padding="4",
        ),
        on_click=rx.call_script(f"window.location.href='{route}'"),
        cursor="pointer",
        _hover={"box_shadow": "0 4px 16px rgba(0,0,0,0.10)"},
        transition="box-shadow 0.2s",
        width="240px",
    )


@rx.page(route="/admin", on_load=[AuthState.load_user, AdminState.load_stats])
def admin_page() -> rx.Component:
    return rx.box(
        admin_nav_bar(),
        rx.center(
            rx.vstack(
                rx.heading("平台總覽", size="6"),
                rx.text(
                    "全平台使用者、答題數與題庫量",
                    color=rx.color("gray", 10),
                    size="2",
                ),

                # 統計卡片
                rx.cond(
                    AdminState.is_stats_loading,
                    rx.center(rx.spinner(size="3"), padding_y="8"),
                    rx.vstack(
                        rx.hstack(
                            stat_card("總使用者", AdminState.total_users, "users", "blue"),
                            stat_card("啟用中", AdminState.active_users, "user-check", "green"),
                            stat_card("老師", AdminState.teacher_count, "graduation-cap", "violet"),
                            stat_card("管理員", AdminState.admin_count, "shield", "red"),
                            spacing="3",
                            width="100%",
                        ),
                        rx.hstack(
                            stat_card("已完成測驗場數", AdminState.total_sessions, "file-text", "cyan"),
                            stat_card("累計答題數", AdminState.total_answers, "check-check", "orange"),
                            stat_card("題庫總題數", AdminState.total_questions, "book-open", "yellow"),
                            spacing="3",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                ),

                # 各科題庫量
                rx.card(
                    rx.vstack(
                        rx.heading("各科題庫題數", size="4"),
                        rx.foreach(AdminState.subject_counts, subject_count_row),
                        spacing="2",
                        width="100%",
                    ),
                    padding="5",
                    width="100%",
                ),

                # 導航卡片
                rx.heading("管理功能", size="5", padding_top="4"),
                rx.hstack(
                    nav_card(
                        "users",
                        "使用者管理",
                        "指派角色、停權帳號",
                        "/admin/users",
                        "blue",
                    ),
                    nav_card(
                        "book-open",
                        "題庫維護",
                        "新增、編輯、刪除題目",
                        "/admin/questions",
                        "violet",
                    ),
                    spacing="4",
                    justify="center",
                    flex_wrap="wrap",
                ),

                width="960px",
                max_width="100%",
                spacing="5",
                padding="6",
            ),
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
