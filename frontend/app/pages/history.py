import reflex as rx
from ..state.history_state import HistoryState, HistoryItem, HistoryDetail
from .home import nav_bar


def detail_row(item: HistoryDetail) -> rx.Component:
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


def detail_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading(HistoryState.detail_subject, size="5"),
                        rx.text(
                            HistoryState.detail_year_sitting,
                            size="2",
                            color=rx.color("gray", 8),
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.vstack(
                        rx.text(
                            HistoryState.detail_score_display,
                            weight="bold",
                            size="5",
                        ),
                        rx.dialog.close(
                            rx.button(
                                rx.icon("x", size=14),
                                "關閉",
                                variant="ghost",
                                color_scheme="gray",
                                size="2",
                            ),
                        ),
                        align="end",
                        spacing="2",
                    ),
                    width="100%",
                    align="start",
                ),
                rx.separator(width="100%"),
                rx.cond(
                    HistoryState.is_detail_loading,
                    rx.center(rx.spinner(size="3"), padding_y="8", width="100%"),
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
                            rx.foreach(HistoryState.detail_items, detail_row),
                        ),
                        width="100%",
                        variant="surface",
                    ),
                ),
                spacing="4",
                width="100%",
            ),
            max_width="720px",
            max_height="80vh",
            overflow_y="auto",
        ),
        open=HistoryState.is_detail_open,
        on_open_change=HistoryState.set_is_detail_open,
    )


def session_card(item: HistoryItem) -> rx.Component:
    return rx.card(
        rx.hstack(
            # ── 左側：科目、年份、模式 ──
            rx.vstack(
                rx.text(item.subject_name, weight="bold", size="3"),
                rx.text(
                    item.year_label,
                    size="2",
                    color=rx.color("gray", 9),
                ),
                rx.hstack(
                    rx.badge(item.mode_label, color_scheme="blue", variant="soft"),
                    rx.cond(
                        item.timed,
                        rx.badge(
                            rx.icon("timer", size=12),
                            "計時",
                            color_scheme="orange",
                            variant="soft",
                        ),
                        rx.box(),
                    ),
                    spacing="2",
                    align="center",
                ),
                spacing="2",
                align="start",
            ),
            rx.spacer(),
            # ── 右側：分數、百分比、日期 ──
            rx.vstack(
                rx.text(
                    item.score, " / ", item.question_count,
                    weight="bold",
                    size="5",
                    color=rx.cond(
                        item.percentage >= 60,
                        rx.color("green", 9),
                        rx.color("red", 9),
                    ),
                ),
                rx.text(
                    item.percentage, " %",
                    size="2",
                    color=rx.cond(
                        item.percentage >= 60,
                        rx.color("green", 9),
                        rx.color("red", 9),
                    ),
                ),
                rx.text(item.finished_at, size="1", color=rx.color("gray", 8)),
                align="end",
                spacing="1",
            ),
            width="100%",
            align="center",
        ),
        on_click=HistoryState.load_detail(item.session_id),
        cursor="pointer",
        _hover={"box_shadow": "0 2px 12px rgba(0,0,0,0.10)"},
        transition="box-shadow 0.15s",
        width="100%",
        padding="4",
    )


@rx.page(route="/history", on_load=HistoryState.load_history)
def history_page() -> rx.Component:
    return rx.box(
        nav_bar(),
        detail_dialog(),
        rx.center(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=16),
                        "返回",
                        on_click=rx.redirect("/home"),
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                    ),
                    rx.heading("測驗歷史紀錄", size="6"),
                    align="center",
                    spacing="4",
                ),
                rx.cond(
                    HistoryState.is_loading,
                    rx.center(rx.spinner(size="3"), padding_y="16"),
                    rx.cond(
                        HistoryState.has_history,
                        rx.vstack(
                            rx.foreach(HistoryState.items, session_card),
                            spacing="4",
                            width="100%",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("inbox", size=48, color=rx.color("gray", 6)),
                                rx.text("尚無測驗紀錄", color=rx.color("gray", 8), size="3"),
                                align="center",
                                spacing="3",
                            ),
                            padding_y="16",
                        ),
                    ),
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
