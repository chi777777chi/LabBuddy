import reflex as rx
from ..state.auth_state import AuthState
from ..state.analytics_state import AnalyticsState
from .home import nav_bar


def subject_card(s: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(s["subject_name"], size="1", color=rx.color("gray", 10), weight="medium"),
            rx.heading(
                rx.cond(
                    s["accuracy_rate"] != None,
                    s["accuracy_rate"].to_string() + "%",
                    "—",
                ),
                size="6",
                color=rx.cond(
                    s["accuracy_rate"] != None,
                    rx.color(s["color"], 9),
                    rx.color("gray", 7),
                ),
            ),
            rx.text(
                s["correct_count"].to_string(), " / ", s["total_answered"].to_string(), " 題答對",
                size="1",
                color=rx.color("gray", 9),
            ),
            spacing="1",
            align="center",
        ),
        padding="4",
        text_align="center",
        width="100%",
    )


def score_trend_chart() -> rx.Component:
    return rx.cond(
        AnalyticsState.score_trend.length() > 0,
        rx.vstack(
            rx.heading("成績趨勢", size="4"),
            rx.recharts.line_chart(
                rx.recharts.line(
                    data_key="percentage",
                    stroke=rx.color("blue", 9),
                    stroke_width=2,
                    dot=True,
                ),
                rx.recharts.x_axis(data_key="date", tick={"fontSize": 11}),
                rx.recharts.y_axis(domain=[0, 100], tick={"fontSize": 11}, unit="%"),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                rx.recharts.graphing_tooltip(),
                data=AnalyticsState.score_trend,
                width="100%",
                height=220,
            ),
            width="100%",
            spacing="3",
        ),
        rx.fragment(),
    )


def weak_questions_list() -> rx.Component:
    return rx.cond(
        AnalyticsState.weak_questions.length() > 0,
        rx.vstack(
            rx.heading("最常答錯題目", size="4"),
            rx.vstack(
                rx.foreach(
                    AnalyticsState.weak_questions,
                    lambda w: rx.card(
                        rx.hstack(
                            rx.vstack(
                                rx.hstack(
                                    rx.badge(w["subject_name"], color_scheme="blue", variant="soft", size="1"),
                                    rx.badge(w["source"], color_scheme="gray", variant="soft", size="1"),
                                    spacing="2",
                                ),
                                rx.text(w["content"], size="2"),
                                spacing="1",
                                align="start",
                            ),
                            rx.spacer(),
                            rx.vstack(
                                rx.badge(
                                    rx.icon("circle-x", size=12),
                                    w["wrong_count"].to_string(), " 錯",
                                    color_scheme="red", variant="soft", size="2",
                                ),
                                rx.badge(
                                    rx.icon("circle-check", size=12),
                                    w["correct_count"].to_string(), " 對",
                                    color_scheme="green", variant="soft", size="2",
                                ),
                                spacing="1",
                                align="end",
                            ),
                            align="start",
                            width="100%",
                        ),
                        width="100%",
                        padding="3",
                    ),
                ),
                width="100%",
                spacing="2",
            ),
            width="100%",
            spacing="3",
        ),
        rx.fragment(),
    )


def ai_analysis_card() -> rx.Component:
    return rx.cond(
        AnalyticsState.ai_analysis != "",
        rx.vstack(
            rx.heading("AI 學習建議", size="4"),
            rx.card(
                rx.hstack(
                    rx.icon("sparkles", size=16, color=rx.color("violet", 9)),
                    rx.text("由 Groq AI 生成", size="1", color=rx.color("violet", 9)),
                    spacing="2",
                    align="center",
                ),
                rx.divider(margin_y="2"),
                rx.text(
                    AnalyticsState.ai_analysis,
                    size="2",
                    line_height="1.9",
                    white_space="pre-wrap",
                ),
                width="100%",
                padding="5",
            ),
            width="100%",
            spacing="3",
        ),
        rx.fragment(),
    )


@rx.page(route="/analytics", on_load=[AuthState.load_user, AnalyticsState.load_analytics])
def analytics_page() -> rx.Component:
    return rx.box(
        nav_bar(),
        rx.center(
            rx.cond(
                ~AnalyticsState.has_loaded,
                rx.center(
                    rx.vstack(
                        rx.spinner(size="3"),
                        rx.text("AI 分析資料中，請稍候…", size="3", color=rx.color("gray", 9)),
                        spacing="4",
                        align="center",
                    ),
                    padding_top="20",
                ),
                rx.cond(
                    AnalyticsState.error_msg != "",
                    rx.center(
                        rx.vstack(
                            rx.icon("wifi-off", size=40, color=rx.color("red", 7)),
                            rx.text(AnalyticsState.error_msg, size="3", color=rx.color("red", 9)),
                            rx.button("重新載入", on_click=AnalyticsState.load_analytics, color_scheme="blue", size="2"),
                            spacing="4",
                            align="center",
                            padding_top="20",
                        ),
                    ),
                    rx.cond(
                        AnalyticsState.has_data,
                    rx.vstack(
                        rx.heading("學習分析", size="6"),
                        # 科目答對率
                        rx.vstack(
                            rx.heading("各科答對率", size="4"),
                            rx.grid(
                                rx.foreach(AnalyticsState.subject_stats, subject_card),
                                columns="3",
                                spacing="3",
                                width="100%",
                            ),
                            width="100%",
                            spacing="3",
                        ),
                        score_trend_chart(),
                        weak_questions_list(),
                        ai_analysis_card(),
                        rx.hstack(
                            rx.button(
                                rx.icon("house", size=15),
                                "回主選單",
                                on_click=rx.redirect("/home"),
                                variant="soft",
                                color_scheme="gray",
                                size="2",
                            ),
                            rx.button(
                                rx.icon("pencil", size=15),
                                "開始練習",
                                on_click=rx.redirect("/exam-setup"),
                                variant="soft",
                                color_scheme="blue",
                                size="2",
                            ),
                            rx.button(
                                rx.icon("bookmark-x", size=15),
                                "錯題複習",
                                on_click=rx.redirect("/wrong-review"),
                                variant="soft",
                                color_scheme="red",
                                size="2",
                            ),
                            spacing="3",
                            padding_top="2",
                        ),
                        width="760px",
                        max_width="100%",
                        spacing="7",
                        padding="6",
                        align="start",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("bar-chart-2", size=48, color=rx.color("gray", 6)),
                            rx.heading("尚無作答記錄", size="5", color=rx.color("gray", 8)),
                            rx.text("完成幾場測驗後，這裡會顯示你的學習分析。", color=rx.color("gray", 9), size="3"),
                            rx.button(
                                "前往練習",
                                on_click=rx.redirect("/exam-setup"),
                                color_scheme="blue",
                                size="3",
                            ),
                            spacing="4",
                            align="center",
                            padding_top="20",
                        ),
                    ),
                ),
                ),
            ),
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
