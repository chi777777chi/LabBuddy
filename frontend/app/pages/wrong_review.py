import reflex as rx
from ..state.wrong_review_state import WrongReviewState, SubjectStat
from ..state.exam_state import ExamState
from .home import nav_bar


def subject_stat_card(item: SubjectStat) -> rx.Component:
    total_attempts = item.total_wrong + item.total_correct
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(item.subject_name, weight="bold", size="3"),
                rx.hstack(
                    rx.badge(
                        item.wrong_question_count, " 題有錯誤",
                        color_scheme="red",
                        variant="soft",
                    ),
                    rx.text(
                        "共答 ", total_attempts, " 次",
                        size="2",
                        color=rx.color("gray", 9),
                    ),
                    spacing="3",
                    align="center",
                ),
                rx.text(
                    rx.text.span("答錯 ", color=rx.color("red", 9)),
                    rx.text.span(item.total_wrong, weight="bold", color=rx.color("red", 9)),
                    rx.text.span(" 次　", color=rx.color("red", 9)),
                    rx.text.span("答對 ", color=rx.color("green", 9)),
                    rx.text.span(item.total_correct, weight="bold", color=rx.color("green", 9)),
                    rx.text.span(" 次", color=rx.color("green", 9)),
                    size="2",
                ),
                spacing="2",
                align="start",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("rotate-ccw", size=15),
                "開始複習",
                on_click=ExamState.start_wrong_review(item.subject_id),
                color_scheme="orange",
                size="2",
            ),
            width="100%",
            align="center",
        ),
        width="100%",
        padding="4",
    )


@rx.page(route="/wrong-review", on_load=WrongReviewState.load_stats)
def wrong_review_page() -> rx.Component:
    return rx.box(
        nav_bar(),
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
                    rx.heading("錯題複習", size="6"),
                    align="center",
                    spacing="4",
                ),
                rx.text(
                    "依科目顯示你有答錯紀錄的題目，優先複習答錯最多次的題目",
                    size="2",
                    color=rx.color("gray", 9),
                ),
                rx.cond(
                    WrongReviewState.is_loading,
                    rx.center(rx.spinner(size="3"), padding_y="16"),
                    rx.cond(
                        WrongReviewState.has_wrong_questions,
                        rx.vstack(
                            rx.foreach(WrongReviewState.stats, subject_stat_card),
                            spacing="4",
                            width="100%",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("circle-check", size=48, color=rx.color("green", 6)),
                                rx.text("目前沒有錯題紀錄", color=rx.color("gray", 8), size="3"),
                                rx.text(
                                    "完成幾場測驗後，答錯的題目會在這裡統計",
                                    size="2",
                                    color=rx.color("gray", 7),
                                ),
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
