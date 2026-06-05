import reflex as rx
from ..state.auth_state import AuthState
from ..state.teacher_state import TeacherState
from .teacher import teacher_nav_bar


def subject_stat_card(stat) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(stat["subject_name"], size="1", color=rx.color("gray", 10), weight="medium"),
            rx.heading(stat["avg_score"].to_string(), "%", size="5", color=rx.color("blue", 9)),
            rx.text(stat["session_count"].to_string(), " 場", size="1", color=rx.color("gray", 9)),
            align="center",
            spacing="1",
            padding="2",
        ),
        width="100%",
    )


def session_row(s) -> rx.Component:
    return rx.hstack(
        rx.text(s["date"], size="2", color=rx.color("gray", 9), width="90px"),
        rx.text(s["subject_name"], size="2", weight="medium", flex="1"),
        rx.cond(
            s["year"] != "—",
            rx.text(s["year"], " 年第 ", s["sitting"], " 次", size="1", color=rx.color("gray", 9), width="100px"),
            rx.text("—", size="1", color=rx.color("gray", 9), width="100px"),
        ),
        rx.badge(s["score"].to_string(), "%", color_scheme="blue", variant="soft"),
        rx.text(s["question_count"].to_string(), " 題", size="1", color=rx.color("gray", 9)),
        rx.icon("chevron-right", size=14, color=rx.color("gray", 7)),
        on_click=TeacherState.load_session_detail(s["session_id"]),
        cursor="pointer",
        width="100%",
        align="center",
        spacing="3",
        padding_y="2",
        border_bottom=f"1px solid {rx.color('gray', 3)}",
        _hover={"background": rx.color("gray", 2)},
        border_radius="4px",
        padding_x="2",
    )


def session_detail_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.heading(TeacherState.session_detail_label, size="4"),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.button(
                            rx.icon("x", size=16),
                            variant="ghost",
                            color_scheme="gray",
                            size="1",
                        ),
                    ),
                    width="100%",
                    align="center",
                ),
                rx.separator(width="100%"),
                rx.cond(
                    TeacherState.session_detail_loading,
                    rx.center(rx.spinner(size="3"), padding_y="6"),
                    rx.cond(
                        TeacherState.session_detail_items.length() > 0,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("#", width="40px"),
                                    rx.table.column_header_cell("題目"),
                                    rx.table.column_header_cell("作答", width="60px"),
                                    rx.table.column_header_cell("正解", width="60px"),
                                    rx.table.column_header_cell("結果", width="50px"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    TeacherState.session_detail_items,
                                    lambda item: rx.table.row(
                                        rx.table.cell(item["order"], justify="center"),
                                        rx.table.cell(
                                            rx.text(item["content"], size="1", no_of_lines=2),
                                        ),
                                        rx.table.cell(
                                            rx.cond(
                                                item["chosen"] != None,
                                                rx.badge(item["chosen"], color_scheme="blue"),
                                                rx.text("未作答", size="1", color=rx.color("gray", 8)),
                                            ),
                                            justify="center",
                                        ),
                                        rx.table.cell(
                                            rx.badge(item["correct_answer"], color_scheme="gray"),
                                            justify="center",
                                        ),
                                        rx.table.cell(
                                            rx.cond(
                                                item["chosen"] == None,
                                                rx.text("—", color=rx.color("gray", 8)),
                                                rx.cond(
                                                    item["is_correct"],
                                                    rx.icon("check", color=rx.color("green", 9), size=16),
                                                    rx.icon("x", color=rx.color("red", 9), size=16),
                                                ),
                                            ),
                                            justify="center",
                                        ),
                                    ),
                                ),
                            ),
                            width="100%",
                            variant="surface",
                        ),
                        rx.text("無資料", color=rx.color("gray", 8), size="2"),
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            max_width="700px",
            max_height="80vh",
            overflow_y="auto",
        ),
        open=TeacherState.show_session_detail,
        on_open_change=lambda v: TeacherState.close_session_detail(),
    )


@rx.page(route="/teacher/student/[class_id]/[student_id]", on_load=[AuthState.load_user, TeacherState.load_student_progress])
def teacher_student_page() -> rx.Component:
    return rx.box(
        session_detail_dialog(),
        teacher_nav_bar(),
        rx.center(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=16),
                        "返回班級",
                        on_click=TeacherState.back_to_class,
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                    ),
                    width="100%",
                ),
                rx.cond(
                    TeacherState.is_student_loading,
                    rx.center(rx.spinner(size="3"), padding_y="8"),
                    rx.vstack(
                        # 學生基本資訊
                        rx.card(
                            rx.hstack(
                                rx.vstack(
                                    rx.heading(TeacherState.viewed_student_name, size="5"),
                                    rx.text(TeacherState.viewed_student_email, size="2", color=rx.color("gray", 9)),
                                    spacing="1",
                                    align="start",
                                ),
                                rx.spacer(),
                                rx.badge(
                                    TeacherState.viewed_class_name,
                                    color_scheme="violet",
                                    variant="soft",
                                ),
                                width="100%",
                                align="center",
                            ),
                            padding="4",
                            width="100%",
                        ),

                        # 各科答對率
                        rx.vstack(
                            rx.heading("各科平均答對率", size="4"),
                            rx.cond(
                                TeacherState.student_subject_stats.length() > 0,
                                rx.grid(
                                    rx.foreach(TeacherState.student_subject_stats, subject_stat_card),
                                    columns="3",
                                    spacing="3",
                                    width="100%",
                                ),
                                rx.text("尚無作答紀錄", color=rx.color("gray", 8), size="2"),
                            ),
                            spacing="3",
                            width="100%",
                        ),

                        # 測驗歷史
                        rx.vstack(
                            rx.heading("最近 20 場測驗", size="4"),
                            rx.cond(
                                TeacherState.student_sessions.length() > 0,
                                rx.vstack(
                                    rx.foreach(TeacherState.student_sessions, session_row),
                                    spacing="0",
                                    width="100%",
                                ),
                                rx.text("尚無測驗紀錄", color=rx.color("gray", 8), size="2"),
                            ),
                            spacing="3",
                            width="100%",
                        ),

                        spacing="5",
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
