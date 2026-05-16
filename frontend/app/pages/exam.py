import reflex as rx
from ..state.exam_state import ExamState


def option_item(
    label: str,
    text_var,
    is_selected: bool,
    is_eliminated: bool,
    is_correct: bool,
    is_wrong: bool,
) -> rx.Component:
    border_color = rx.cond(
        is_correct, rx.color("green", 8),
        rx.cond(is_wrong, rx.color("red", 8),
        rx.cond(is_selected, rx.color("blue", 8), rx.color("gray", 4)))
    )
    bg_color = rx.cond(
        is_correct, rx.color("green", 2),
        rx.cond(is_wrong, rx.color("red", 2),
        rx.cond(is_selected, rx.color("blue", 2), "white"))
    )

    return rx.hstack(
        rx.box(
            rx.hstack(
                rx.badge(
                    label,
                    color_scheme=rx.cond(is_selected, "blue", "gray"),
                    variant="soft",
                    size="2",
                ),
                rx.text(
                    text_var,
                    size="2",
                    text_decoration=rx.cond(is_eliminated, "line-through", "none"),
                    color=rx.cond(is_eliminated, rx.color("gray", 8), "inherit"),
                ),
                align="start",
                spacing="3",
            ),
            flex="1",
            padding="3",
            border_radius="8px",
            border="2px solid",
            border_color=border_color,
            background=bg_color,
            cursor=rx.cond(ExamState.is_current_answered, "default", "pointer"),
            on_click=ExamState.select_option(label),
            transition="all 0.15s",
            _hover={"border_color": rx.cond(ExamState.is_current_answered, border_color, rx.color("blue", 6))},
        ),
        rx.icon_button(
            rx.icon("x", size=14),
            size="1",
            variant="ghost",
            color_scheme=rx.cond(is_eliminated, "red", "gray"),
            on_click=ExamState.toggle_eliminate(label),
            title="刪去此選項",
        ),
        align="center",
        width="100%",
        spacing="2",
    )


def early_submit_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.heading("提早交卷", size="5"),
                rx.cond(
                    ExamState.all_answered,
                    rx.text("確定要提早交卷？", size="3"),
                    rx.hstack(
                        rx.icon("triangle-alert", size=18, color=rx.color("orange", 9)),
                        rx.text(
                            "還有 ",
                            rx.text.span(ExamState.unanswered_count, weight="bold"),
                            " 題未作答，確定要提早交卷？",
                            size="3",
                        ),
                        align="center",
                        spacing="2",
                    ),
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("取消", variant="soft", color_scheme="gray"),
                    ),
                    rx.button(
                        "確定交卷",
                        color_scheme="red",
                        on_click=ExamState.submit_exam,
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="360px",
        ),
        open=ExamState.show_early_submit_dialog,
        on_open_change=ExamState.set_show_early_submit_dialog,
    )


def quit_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.heading("放棄此次測驗？", size="5"),
                rx.text(
                    "作答紀錄不會儲存，確定要返回主選單嗎？",
                    size="3",
                    color=rx.color("gray", 9),
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("繼續作答", variant="soft", color_scheme="gray"),
                    ),
                    rx.button(
                        "確定放棄",
                        color_scheme="red",
                        on_click=ExamState.confirm_quit,
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="380px",
        ),
        open=ExamState.show_quit_dialog,
        on_open_change=ExamState.set_show_quit_dialog,
    )


def top_bar() -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.icon("arrow-left", size=15),
            "返回",
            on_click=ExamState.open_quit_dialog,
            size="2",
            variant="ghost",
            color_scheme="gray",
        ),
        rx.vstack(
            rx.text(ExamState.current_source, size="1", color=rx.color("gray", 10)),
            rx.progress(
                value=ExamState.current_index + 1,
                max=ExamState.total_questions,
                width="200px",
                color_scheme="blue",
            ),
            rx.text(ExamState.progress_text, size="2", weight="bold"),
            spacing="1",
        ),
        rx.spacer(),
        rx.cond(
            ExamState.timed,
            rx.badge(
                rx.icon("timer", size=14),
                ExamState.time_display,
                color_scheme=rx.cond(ExamState.time_left < 30, "red", "blue"),
                size="3",
                variant="solid",
            ),
            rx.fragment(),
        ),
        rx.button(
            rx.icon("flag", size=14),
            "提早交卷",
            on_click=ExamState.open_early_submit_dialog,
            disabled=ExamState.is_loading,
            size="2",
            color_scheme="red",
            variant="soft",
        ),
        width="100%",
        padding_x="6",
        padding_y="3",
        border_bottom=f"1px solid {rx.color('gray', 4)}",
        background="white",
        align="center",
        spacing="3",
    )


def question_area() -> rx.Component:
    return rx.vstack(
        rx.cond(
            ExamState.is_wrong_review,
            rx.hstack(
                rx.badge(
                    rx.icon("x-circle", size=13),
                    "答錯 ", ExamState.current_wrong_count, " 次",
                    color_scheme="red",
                    variant="soft",
                    size="2",
                ),
                rx.badge(
                    rx.icon("check-circle", size=13),
                    "答對 ", ExamState.current_correct_count, " 次",
                    color_scheme="green",
                    variant="soft",
                    size="2",
                ),
                spacing="2",
            ),
            rx.box(),
        ),
        rx.box(
            rx.text(
                rx.text.span(
                    f"第 ",
                    rx.text.span(ExamState.current_index + 1, weight="bold"),
                    " 題　",
                    color=rx.color("blue", 9),
                ),
                ExamState.current_content,
                size="3",
                line_height="1.8",
            ),
            width="100%",
            padding="5",
            background="white",
            border_radius="12px",
            border=f"1px solid {rx.color('gray', 4)}",
        ),
        rx.vstack(
            option_item("A", ExamState.option_a_text, ExamState.selected_a, ExamState.eliminated_a, ExamState.correct_a, ExamState.wrong_a),
            option_item("B", ExamState.option_b_text, ExamState.selected_b, ExamState.eliminated_b, ExamState.correct_b, ExamState.wrong_b),
            option_item("C", ExamState.option_c_text, ExamState.selected_c, ExamState.eliminated_c, ExamState.correct_c, ExamState.wrong_c),
            option_item("D", ExamState.option_d_text, ExamState.selected_d, ExamState.eliminated_d, ExamState.correct_d, ExamState.wrong_d),
            spacing="3",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def nav_buttons() -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.icon("chevron-left", size=16),
            "上一題",
            on_click=ExamState.go_prev,
            disabled=(ExamState.current_index == 0) | ExamState.is_showing_feedback,
            variant="soft",
            color_scheme="gray",
            size="3",
        ),
        rx.spacer(),
        rx.cond(
            ExamState.is_last_question,
            rx.button(
                "交卷",
                rx.icon("check", size=16),
                on_click=ExamState.open_early_submit_dialog,
                disabled=ExamState.is_loading | ExamState.is_showing_feedback,
                color_scheme="green",
                size="3",
            ),
            rx.button(
                "下一題",
                rx.icon("chevron-right", size=16),
                on_click=ExamState.handle_next,
                disabled=ExamState.is_showing_feedback,
                color_scheme="blue",
                size="3",
            ),
        ),
        width="100%",
    )


@rx.page(route="/exam")
def exam_page() -> rx.Component:
    return rx.cond(
        ExamState.has_session,
        rx.box(
            early_submit_dialog(),
            quit_dialog(),
            top_bar(),
            rx.center(
                rx.vstack(
                    question_area(),
                    nav_buttons(),
                    width="680px",
                    max_width="100%",
                    spacing="5",
                    padding="6",
                ),
            ),
            min_height="100vh",
            background=rx.color("gray", 2),
        ),
        rx.center(
            rx.vstack(
                rx.text("沒有進行中的考試"),
                rx.button("回設定頁", on_click=rx.redirect("/exam-setup")),
                align="center",
                spacing="4",
                padding="8",
            ),
        ),
    )
