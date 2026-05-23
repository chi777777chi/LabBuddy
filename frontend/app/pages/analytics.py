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


def time_efficiency_card() -> rx.Component:
    return rx.cond(
        AnalyticsState.time_has_data,
        rx.vstack(
            rx.heading("作答時間效率", size="4"),
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.icon("timer", size=16, color=rx.color("blue", 9)),
                        rx.text("國考標準：100分鐘 / 80題 = 75秒/題", size="2", color=rx.color("gray", 10)),
                        spacing="2",
                        align="center",
                    ),
                    rx.divider(margin_y="2"),
                    rx.hstack(
                        rx.vstack(
                            rx.text("平均作答時間", size="1", color=rx.color("gray", 9)),
                            rx.heading(
                                AnalyticsState.time_avg_seconds.to_string() + " 秒",
                                size="6",
                                color=rx.color(AnalyticsState.time_speed_color, 9),
                            ),
                            rx.text(
                                "速度：", AnalyticsState.time_speed_label,
                                size="1", color=rx.color("gray", 9),
                            ),
                            align="center",
                            spacing="1",
                        ),
                        rx.divider(orientation="vertical", height="60px"),
                        rx.vstack(
                            rx.badge(
                                rx.icon("alarm-clock", size=12),
                                AnalyticsState.time_slow_count.to_string(), " 題超過120秒",
                                color_scheme="red", variant="soft", size="2",
                            ),
                            rx.badge(
                                rx.icon("zap", size=12),
                                AnalyticsState.time_fast_count.to_string(), " 題低於20秒",
                                color_scheme="orange", variant="soft", size="2",
                            ),
                            rx.text(
                                "統計樣本：", AnalyticsState.time_total_with_time.to_string(), " 題",
                                size="1", color=rx.color("gray", 9),
                            ),
                            spacing="2",
                            align="start",
                        ),
                        spacing="5",
                        align="center",
                        width="100%",
                    ),
                    rx.cond(
                        AnalyticsState.time_speed_color == "red",
                        rx.callout(
                            "作答速度偏慢，建議加強對熟悉題型的直覺判斷，減少長時間猶豫。",
                            icon="triangle-alert",
                            color_scheme="red",
                            size="1",
                            width="100%",
                        ),
                        rx.cond(
                            AnalyticsState.time_speed_color == "orange",
                            rx.callout(
                                "作答速度偏快，請注意避免因過快而看錯題意或漏掉關鍵細節。",
                                icon="triangle-alert",
                                color_scheme="orange",
                                size="1",
                                width="100%",
                            ),
                            rx.callout(
                                "作答速度在合理範圍內，繼續保持！",
                                icon="circle-check",
                                color_scheme="green",
                                size="1",
                                width="100%",
                            ),
                        ),
                    ),
                    spacing="3",
                    width="100%",
                ),
                width="100%",
                padding="5",
            ),
            width="100%",
            spacing="3",
        ),
        rx.fragment(),
    )


def subject_badge(s: dict, color: str) -> rx.Component:
    return rx.badge(s["subject_short"], color_scheme=color, variant="solid", size="2")


def highlight_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("重點摘要", size="4"),
            rx.divider(),
            # 科目分類
            rx.vstack(
                rx.cond(
                    AnalyticsState.weak_subjects.length() > 0,
                    rx.hstack(
                        rx.text("需加強", size="2", weight="bold", color=rx.color("red", 9), min_width="60px"),
                        rx.hstack(
                            rx.foreach(AnalyticsState.weak_subjects, lambda s: subject_badge(s, "red")),
                            flex_wrap="wrap",
                            spacing="2",
                        ),
                        align="center",
                        spacing="3",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    AnalyticsState.ok_subjects.length() > 0,
                    rx.hstack(
                        rx.text("可進步", size="2", weight="bold", color=rx.color("orange", 9), min_width="60px"),
                        rx.hstack(
                            rx.foreach(AnalyticsState.ok_subjects, lambda s: subject_badge(s, "orange")),
                            flex_wrap="wrap",
                            spacing="2",
                        ),
                        align="center",
                        spacing="3",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    AnalyticsState.strong_subjects.length() > 0,
                    rx.hstack(
                        rx.text("表現佳", size="2", weight="bold", color=rx.color("green", 9), min_width="60px"),
                        rx.hstack(
                            rx.foreach(AnalyticsState.strong_subjects, lambda s: subject_badge(s, "green")),
                            flex_wrap="wrap",
                            spacing="2",
                        ),
                        align="center",
                        spacing="3",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                spacing="3",
                width="100%",
            ),
            # 成績趨勢
            rx.cond(
                AnalyticsState.trend_direction != "none",
                rx.hstack(
                    rx.text("成績趨勢", size="2", weight="bold", min_width="60px"),
                    rx.cond(
                        AnalyticsState.trend_direction == "improving",
                        rx.badge(rx.icon("trending-up", size=13), "持續進步", color_scheme="green", variant="solid", size="2"),
                        rx.cond(
                            AnalyticsState.trend_direction == "declining",
                            rx.badge(rx.icon("trending-down", size=13), "需要注意", color_scheme="red", variant="solid", size="2"),
                            rx.badge(rx.icon("minus", size=13), "成績平穩", color_scheme="blue", variant="solid", size="2"),
                        ),
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.fragment(),
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        padding="5",
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
                    line_height="2.0",
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
                        time_efficiency_card(),
                        weak_questions_list(),
                        highlight_section(),
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
