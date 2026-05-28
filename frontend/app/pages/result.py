import reflex as rx
from ..state.exam_state import ExamState, ResultDetail  # noqa: F401


def format_seconds(secs: int) -> str:
    mins = secs // 60
    s = secs % 60
    return f"{mins:02d}:{s:02d}"


def time_bar_row(item: ResultDetail) -> rx.Component:
    """各題用時列：只在 time_spent_seconds > 0 時顯示。"""
    bar_width = rx.cond(
        item.time_spent_seconds > 0,
        (item.time_spent_seconds * 200 // 300).to_string() + "px",
        "4px",
    )
    color = rx.cond(
        item.time_spent_seconds > 120, "red",
        rx.cond(item.time_spent_seconds > 75, "orange", "green")
    )
    return rx.hstack(
        rx.text(f"第", rx.text.span(item.order, weight="bold"), "題", size="2", width="52px"),
        rx.box(
            rx.box(
                height="10px",
                width=bar_width,
                background=rx.cond(
                    item.time_spent_seconds > 120, rx.color("red", 7),
                    rx.cond(item.time_spent_seconds > 75, rx.color("orange", 7), rx.color("green", 7))
                ),
                border_radius="4px",
                max_width="200px",
            ),
            background=rx.color("gray", 3),
            border_radius="4px",
            width="200px",
            height="10px",
            overflow="hidden",
        ),
        rx.text(item.time_spent_seconds, " 秒", size="1", color=rx.color("gray", 10), width="50px"),
        rx.cond(
            item.time_spent_seconds > 120,
            rx.badge("偏慢", color_scheme="red", size="1"),
            rx.cond(
                item.time_spent_seconds > 75,
                rx.badge("稍慢", color_scheme="orange", size="1"),
                rx.fragment(),
            ),
        ),
        align="center",
        spacing="3",
        width="100%",
    )


def detail_row(item: ResultDetail) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item.order, justify="center"),
        rx.table.cell(
            rx.vstack(
                rx.text(item.content, size="1", no_of_lines=2),
                rx.button(
                    rx.icon("sparkles", size=12),
                    "AI 解析",
                    size="1",
                    variant="ghost",
                    color_scheme="violet",
                    on_click=ExamState.fetch_explain(item.question_id, item.chosen, item.order),
                ),
                align="start",
                spacing="1",
            ),
        ),
        rx.table.cell(
            rx.cond(
                item.is_unanswered,
                rx.text("未作答", color=rx.color("gray", 8), size="1"),
                rx.badge(item.chosen, color_scheme="blue"),
            ),
            justify="center",
        ),
        rx.table.cell(
            rx.badge(item.correct_answer, color_scheme="gray"),
            justify="center",
        ),
        rx.table.cell(
            rx.cond(
                item.is_unanswered,
                rx.text("—", color=rx.color("gray", 8)),
                rx.cond(
                    item.is_correct,
                    rx.icon("check", color=rx.color("green", 9), size=18),
                    rx.icon("x", color=rx.color("red", 9), size=18),
                ),
            ),
            justify="center",
        ),
    )


def explain_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("sparkles", size=20, color=rx.color("violet", 9)),
                    rx.heading(ExamState.explain_question_label + " AI 解析", size="5"),
                    align="center",
                    spacing="2",
                ),
                rx.separator(width="100%"),
                rx.cond(
                    ExamState.explain_loading,
                    rx.center(
                        rx.vstack(
                            rx.spinner(size="3"),
                            rx.text("AI 正在分析中…", size="2", color=rx.color("gray", 8)),
                            align="center",
                            spacing="3",
                        ),
                        padding_y="8",
                        width="100%",
                    ),
                    rx.text(ExamState.explain_text, size="2", white_space="pre-wrap"),
                ),
                rx.dialog.close(
                    rx.button("關閉", variant="ghost", color_scheme="gray", size="2"),
                ),
                spacing="4",
                width="100%",
            ),
            max_width="600px",
            max_height="80vh",
            overflow_y="auto",
        ),
        open=ExamState.show_explain_dialog,
        on_open_change=ExamState.set_show_explain_dialog,
    )


@rx.page(route="/result")
def result_page() -> rx.Component:
    return rx.box(
        explain_dialog(),
        rx.center(
            rx.vstack(
                rx.card(
                    rx.vstack(
                        rx.heading("測驗結果", size="6"),
                        rx.hstack(
                            rx.vstack(
                                rx.hstack(
                                    rx.text(ExamState.result_score, size="8", weight="bold", color=rx.color("blue", 9)),
                                    rx.text(" / ", size="5", color=rx.color("gray", 8)),
                                    rx.text(ExamState.result_total, size="8", weight="bold", color=rx.color("blue", 9)),
                                    align="center",
                                    spacing="1",
                                ),
                                rx.text("答對題數", size="2", color=rx.color("gray", 10)),
                                align="center",
                            ),
                            rx.separator(orientation="vertical", size="3"),
                            rx.vstack(
                                rx.text(ExamState.result_percentage, " %", size="8", weight="bold", color=rx.color("green", 9)),
                                rx.text("答對率", size="2", color=rx.color("gray", 10)),
                                align="center",
                            ),
                            rx.cond(
                                ExamState.result_elapsed_seconds > 0,
                                rx.fragment(
                                    rx.separator(orientation="vertical", size="3"),
                                    rx.vstack(
                                        rx.hstack(
                                            rx.icon("timer", size=18, color=rx.color("violet", 9)),
                                            rx.text(ExamState.result_time_display, size="6", weight="bold", color=rx.color("violet", 9)),
                                            align="center",
                                            spacing="1",
                                        ),
                                        rx.text("作答時間", size="2", color=rx.color("gray", 10)),
                                        align="center",
                                    ),
                                ),
                                rx.fragment(),
                            ),
                            spacing={"initial": "4", "sm": "8"},
                            justify="center",
                            flex_wrap="wrap",
                            width="100%",
                            padding_y="4",
                        ),
                        rx.hstack(
                            rx.button(
                                rx.icon("rotate-ccw", size=16),
                                "再做一次",
                                on_click=ExamState.restart_exam,
                                variant="soft",
                                color_scheme="blue",
                            ),
                            rx.button(
                                rx.icon("file-down", size=16),
                                "匯出 PDF",
                                on_click=ExamState.download_result_pdf,
                                variant="soft",
                                color_scheme="green",
                            ),
                            rx.button(
                                rx.icon("clock", size=16),
                                "歷史紀錄",
                                on_click=rx.redirect("/history"),
                                variant="soft",
                                color_scheme="violet",
                            ),
                            rx.button(
                                rx.icon("home", size=16),
                                "回主選單",
                                on_click=rx.redirect("/home"),
                                variant="soft",
                                color_scheme="gray",
                            ),
                            spacing="3",
                            flex_wrap="wrap",
                            justify="center",
                        ),
                        align="center",
                        spacing="5",
                    ),
                    width="100%",
                    padding="6",
                ),
                rx.card(
                    rx.vstack(
                        rx.heading("各題回顧", size="4"),
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("題號"),
                                    rx.table.column_header_cell("題目"),
                                    rx.table.column_header_cell("你的答案"),
                                    rx.table.column_header_cell("正確答案"),
                                    rx.table.column_header_cell("對錯"),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(ExamState.result_details, detail_row),
                            ),
                            width="100%",
                            variant="surface",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    width="100%",
                    padding="5",
                ),
                rx.cond(
                    ExamState.result_show_time_breakdown & (ExamState.result_elapsed_seconds > 0),
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("clock", size=18, color=rx.color("violet", 9)),
                                rx.heading("各題用時分析", size="4"),
                                spacing="2",
                                align="center",
                            ),
                            rx.text(
                                "花較多時間的題目，可能代表該主題概念較不熟悉，可優先複習。",
                                size="2",
                                color=rx.color("gray", 10),
                            ),
                            rx.divider(),
                            rx.foreach(ExamState.result_details, time_bar_row),
                            spacing="3",
                            width="100%",
                        ),
                        width="100%",
                        padding="5",
                    ),
                    rx.fragment(),
                ),
                width="760px",
                max_width="100%",
                spacing="5",
                padding="6",
            ),
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
