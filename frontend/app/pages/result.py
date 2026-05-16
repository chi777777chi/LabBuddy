import reflex as rx
from ..state.exam_state import ExamState, ResultDetail  # noqa: F401


def detail_row(item: ResultDetail) -> rx.Component:
    return rx.table.row(
        rx.table.cell(item.order, justify="center"),
        rx.table.cell(
            rx.text(item.content, size="1", no_of_lines=2),
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


@rx.page(route="/result")
def result_page() -> rx.Component:
    return rx.box(
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
                            spacing="8",
                            justify="center",
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
                width="760px",
                max_width="100%",
                spacing="5",
                padding="6",
            ),
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
