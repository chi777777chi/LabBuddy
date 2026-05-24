import reflex as rx
from ..state.auth_state import AuthState
from ..state.teacher_state import TeacherState
from .teacher import teacher_nav_bar


def subject_stat_row(stat) -> rx.Component:
    return rx.hstack(
        rx.text(stat["subject_name"], size="2", weight="medium", flex="1"),
        rx.text(
            stat["participant_count"].to_string(), " 人・",
            stat["total_sessions"].to_string(), " 場",
            size="1",
            color=rx.color("gray", 9),
        ),
        rx.badge(
            stat["avg_score"].to_string(), "%",
            color_scheme=stat["score_color"],
            variant="soft",
        ),
        width="100%",
        align="center",
        spacing="3",
        padding_y="3",
        border_bottom=f"1px solid {rx.color('gray', 3)}",
    )


def wrong_question_row(q) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    q["subject_name"],
                    color_scheme="blue",
                    variant="soft",
                    size="1",
                ),
                rx.text(
                    q["year"].to_string(), " 年第 ", q["sitting"].to_string(), " 次 第 ", q["number"].to_string(), " 題",
                    size="1",
                    color=rx.color("gray", 9),
                ),
                spacing="2",
                align="center",
            ),
            rx.text(q["content_short"], size="2"),
            spacing="1",
            align="start",
            flex="1",
        ),
        rx.vstack(
            rx.badge(
                q["wrong_rate"].to_string(), "% 錯誤率",
                color_scheme="red",
                variant="soft",
            ),
            rx.text(
                q["wrong_count"].to_string(), "/", q["total_attempts"].to_string(), " 人答錯",
                size="1",
                color=rx.color("gray", 9),
            ),
            align="end",
            spacing="1",
        ),
        width="100%",
        align="start",
        spacing="3",
        padding_y="3",
        border_bottom=f"1px solid {rx.color('gray', 3)}",
    )


@rx.page(route="/teacher/stats/[class_id]", on_load=[AuthState.load_user, TeacherState.load_class_stats])
def teacher_stats_page() -> rx.Component:
    return rx.box(
        teacher_nav_bar(),
        rx.center(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=16),
                        "返回班級",
                        on_click=TeacherState.back_from_stats,
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                    ),
                    rx.heading(TeacherState.stats_class_name, "・全班統計", size="5"),
                    align="center",
                    spacing="4",
                    width="100%",
                ),
                rx.cond(
                    TeacherState.is_stats_loading,
                    rx.center(rx.spinner(size="3"), padding_y="8"),
                    rx.vstack(
                        # 各科平均答對率
                        rx.card(
                            rx.vstack(
                                rx.heading("各科平均答對率", size="4"),
                                rx.text(
                                    "排序：由低到高（最弱科目在上）",
                                    size="1",
                                    color=rx.color("gray", 9),
                                ),
                                rx.cond(
                                    TeacherState.class_subject_stats.length() > 0,
                                    rx.vstack(
                                        rx.foreach(TeacherState.class_subject_stats, subject_stat_row),
                                        spacing="0",
                                        width="100%",
                                    ),
                                    rx.text("尚無作答紀錄", color=rx.color("gray", 8), size="2"),
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            padding="5",
                            width="100%",
                        ),

                        # 全班最常答錯題目
                        rx.card(
                            rx.vstack(
                                rx.heading("全班最常答錯題目 Top 10", size="4"),
                                rx.text(
                                    "依全班錯誤次數排序",
                                    size="1",
                                    color=rx.color("gray", 9),
                                ),
                                rx.cond(
                                    TeacherState.top_wrong_questions.length() > 0,
                                    rx.vstack(
                                        rx.foreach(TeacherState.top_wrong_questions, wrong_question_row),
                                        spacing="0",
                                        width="100%",
                                    ),
                                    rx.text("尚無錯誤紀錄", color=rx.color("gray", 8), size="2"),
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            padding="5",
                            width="100%",
                        ),

                        spacing="4",
                        width="100%",
                    ),
                ),
                width="760px",
                max_width="100%",
                spacing="4",
                padding="6",
            ),
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
