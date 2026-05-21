import reflex as rx
from ..state.auth_state import AuthState
from ..state.profile_state import ProfileState
from .home import nav_bar


def stat_card(icon: str, label: str, value, color: str = "blue") -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon(icon, size=28, color=rx.color(color, 9)),
            rx.heading(value, size="6"),
            rx.text(label, size="1", color=rx.color("gray", 9)),
            spacing="2",
            align="center",
        ),
        padding="5",
        text_align="center",
        width="100%",
    )


@rx.page(route="/profile", on_load=[AuthState.load_user, ProfileState.load_stats])
def profile_page() -> rx.Component:
    return rx.box(
        nav_bar(),
        rx.center(
            rx.vstack(
                # ── 使用者資訊卡 ──────────────────────────────────
                rx.card(
                    rx.hstack(
                        rx.avatar(
                            src=AuthState.user_avatar,
                            fallback=AuthState.user_name,
                            size="7",
                        ),
                        rx.vstack(
                            rx.heading(AuthState.user_name, size="5"),
                            rx.text(AuthState.user_email, size="2", color=rx.color("gray", 9)),
                            rx.badge(
                                rx.icon("calendar", size=12),
                                "加入於 ", ProfileState.joined_date,
                                color_scheme="gray",
                                variant="soft",
                                size="1",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        spacing="5",
                        align="center",
                        width="100%",
                    ),
                    width="100%",
                    padding="6",
                ),
                # ── 學習統計 ──────────────────────────────────────
                rx.vstack(
                    rx.heading("學習統計", size="4"),
                    rx.grid(
                        stat_card(
                            "clipboard-list", "完成測驗",
                            ProfileState.total_sessions.to_string() + " 場",
                            "blue",
                        ),
                        stat_card(
                            "pencil", "總作答題數",
                            ProfileState.total_answered.to_string() + " 題",
                            "green",
                        ),
                        stat_card(
                            "percent", "整體答對率",
                            rx.cond(
                                ProfileState.overall_accuracy != None,
                                ProfileState.overall_accuracy.to_string() + "%",
                                "—",
                            ),
                            "orange",
                        ),
                        stat_card(
                            "star", "最常練習科目",
                            rx.cond(
                                ProfileState.favorite_subject != "",
                                ProfileState.favorite_subject,
                                "—",
                            ),
                            "violet",
                        ),
                        columns="2",
                        spacing="3",
                        width="100%",
                    ),
                    width="100%",
                    spacing="3",
                ),
                # ── 快速導航 ──────────────────────────────────────
                rx.vstack(
                    rx.heading("快速前往", size="4"),
                    rx.hstack(
                        rx.button(
                            rx.icon("pencil", size=15),
                            "開始練習",
                            on_click=rx.redirect("/exam-setup"),
                            color_scheme="blue",
                            size="2",
                        ),
                        rx.button(
                            rx.icon("clock", size=15),
                            "歷史紀錄",
                            on_click=rx.redirect("/history"),
                            variant="soft",
                            color_scheme="gray",
                            size="2",
                        ),
                        rx.button(
                            rx.icon("bookmark-x", size=15),
                            "錯題複習",
                            on_click=rx.redirect("/wrong-review"),
                            variant="soft",
                            color_scheme="gray",
                            size="2",
                        ),
                        rx.button(
                            rx.icon("bar-chart-2", size=15),
                            "學習分析",
                            on_click=rx.redirect("/analytics"),
                            variant="soft",
                            color_scheme="violet",
                            size="2",
                        ),
                        rx.button(
                            rx.icon("house", size=15),
                            "回主選單",
                            on_click=rx.redirect("/home"),
                            variant="soft",
                            color_scheme="gray",
                            size="2",
                        ),
                        spacing="3",
                        flex_wrap="wrap",
                    ),
                    width="100%",
                    spacing="3",
                ),
                width="600px",
                max_width="100%",
                spacing="6",
                padding="6",
                align="start",
            ),
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
