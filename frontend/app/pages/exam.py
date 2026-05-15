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
            cursor="pointer",
            on_click=ExamState.select_option(label),
            transition="all 0.15s",
            _hover={"border_color": rx.color("blue", 6)},
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


def top_bar() -> rx.Component:
    return rx.hstack(
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
            on_click=ExamState.submit_exam,
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
            disabled=ExamState.current_index == 0,
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
                on_click=ExamState.submit_exam,
                disabled=ExamState.is_loading,
                color_scheme="green",
                size="3",
            ),
            rx.button(
                "下一題",
                rx.icon("chevron-right", size=16),
                on_click=ExamState.go_next,
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
