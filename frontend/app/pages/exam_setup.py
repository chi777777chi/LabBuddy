import reflex as rx
from ..state.auth_state import AuthState
from ..state.exam_state import ExamState
from .home import nav_bar


def subject_select() -> rx.Component:
    return rx.vstack(
        rx.text("科目", weight="bold", size="2"),
        rx.select.root(
            rx.select.trigger(placeholder="選擇科目", width="100%"),
            rx.select.content(
                rx.foreach(
                    ExamState.subjects,
                    lambda s: rx.select.item(s["name"], value=s["id"].to_string()),
                ),
            ),
            value=ExamState.selected_subject_id.to_string(),
            on_change=ExamState.set_subject,
            width="100%",
        ),
        align="start",
        width="100%",
    )


def mode_select() -> rx.Component:
    modes = [
        ("single_full",   "單份完整（指定年份梯次，依序出題）"),
        ("single_random", "單份隨機（從單份隨機抽題）"),
        ("multi_random",  "多份隨機（跨所有考古題隨機抽題）"),
        ("adaptive",      "自適應（依你的弱點加權出題，答錯越多越常出現）"),
    ]
    return rx.vstack(
        rx.text("出題模式", weight="bold", size="2"),
        rx.radio_group.root(
            rx.vstack(
                *[
                    rx.hstack(
                        rx.radio_group.item(value=val),
                        rx.text(label, size="2"),
                        align="center",
                        spacing="2",
                    )
                    for val, label in modes
                ],
                spacing="2",
            ),
            value=ExamState.selected_mode,
            on_change=ExamState.set_mode,
        ),
        align="start",
        width="100%",
    )


def difficulty_select() -> rx.Component:
    difficulties = [
        ("all",    "全部"),
        ("easy",   "簡單"),
        ("medium", "中等"),
        ("hard",   "困難"),
    ]
    return rx.cond(
        ExamState.selected_mode != "wrong_review",
        rx.vstack(
            rx.text("難度篩選", weight="bold", size="2"),
            rx.radio_group.root(
                rx.hstack(
                    *[
                        rx.hstack(
                            rx.radio_group.item(value=val),
                            rx.text(label, size="2"),
                            align="center",
                            spacing="2",
                        )
                        for val, label in difficulties
                    ],
                    spacing="5",
                ),
                value=ExamState.selected_difficulty,
                on_change=ExamState.set_difficulty,
            ),
            align="start",
            width="100%",
        ),
        rx.fragment(),
    )


def year_sitting_select() -> rx.Component:
    return rx.cond(
        (ExamState.selected_mode != "multi_random") & (ExamState.selected_mode != "adaptive"),
        rx.vstack(
            rx.text("考古題年份／梯次", weight="bold", size="2"),
            rx.select.root(
                rx.select.trigger(width="200px"),
                rx.select.content(
                    rx.foreach(
                        ExamState.available_exams,
                        lambda e: rx.select.item(e["label"], value=e["combo"]),
                    ),
                ),
                value=ExamState.selected_exam_value,
                on_change=ExamState.set_exam,
            ),
            align="start",
            width="100%",
        ),
        rx.fragment(),
    )


def count_select() -> rx.Component:
    counts = [("5", "5 題"), ("10", "10 題"), ("80", "80 題（完整）")]
    return rx.vstack(
        rx.text("題數", weight="bold", size="2"),
        rx.radio_group.root(
            rx.hstack(
                *[
                    rx.hstack(
                        rx.radio_group.item(value=val),
                        rx.text(label, size="2"),
                        align="center",
                        spacing="2",
                    )
                    for val, label in counts
                ],
                spacing="5",
            ),
            value=ExamState.selected_count.to_string(),
            on_change=ExamState.set_count,
        ),
        align="start",
        width="100%",
    )


def options_toggles() -> rx.Component:
    return rx.vstack(
        rx.text("輔助選項", weight="bold", size="2"),
        rx.hstack(
            rx.switch(checked=ExamState.shuffle_options, on_change=ExamState.toggle_shuffle),
            rx.text("選項順序隨機", size="2"),
            align="center",
        ),
        rx.hstack(
            rx.switch(checked=ExamState.timed, on_change=ExamState.toggle_timed),
            rx.text("開啟計時（記錄本場作答時間）", size="2"),
            align="center",
        ),
        rx.cond(
            ExamState.timed,
            rx.hstack(
                rx.box(width="28px"),
                rx.switch(checked=ExamState.show_time_breakdown, on_change=ExamState.toggle_time_breakdown),
                rx.text("作答後顯示各題用時分析（推測弱點主題）", size="2", color=rx.color("gray", 11)),
                align="center",
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.switch(checked=ExamState.instant_review, on_change=ExamState.toggle_instant_review),
            rx.text("即時對答（答完每題立即顯示對錯）", size="2"),
            align="center",
        ),
        rx.hstack(
            rx.switch(checked=ExamState.save_to_history, on_change=ExamState.toggle_save_history),
            rx.text("儲存至歷史紀錄", size="2"),
            align="center",
        ),
        rx.hstack(
            rx.switch(checked=ExamState.use_ai_hint, on_change=ExamState.toggle_ai_hint),
            rx.text("AI 提示（答題中可查看 Gemini 分析）", size="2"),
            align="center",
        ),
        align="start",
        spacing="3",
        width="100%",
    )


@rx.page(route="/exam-setup", on_load=[ExamState.load_subjects, ExamState.load_available_exams, AuthState.load_user])
def exam_setup_page() -> rx.Component:
    return rx.box(
        nav_bar(),
        rx.center(
            rx.card(
                rx.vstack(
                    rx.heading("測驗設定", size="5"),
                    rx.divider(),
                    subject_select(),
                    mode_select(),
                    year_sitting_select(),
                    difficulty_select(),
                    count_select(),
                    options_toggles(),
                    rx.cond(
                        ExamState.error_msg != "",
                        rx.callout(ExamState.error_msg, color="red"),
                        rx.fragment(),
                    ),
                    rx.cond(
                        (ExamState.selected_mode != "multi_random") & (ExamState.selected_mode != "adaptive"),
                        rx.text(
                            "已選擇：",
                            rx.text.span(ExamState.selected_exam_label, weight="bold", color=rx.color("blue", 9)),
                            size="2",
                            color=rx.color("gray", 10),
                        ),
                        rx.fragment(),
                    ),
                    rx.button(
                        rx.cond(
                            ExamState.is_loading | ExamState.is_loading_exams,
                            rx.spinner(size="2"),
                            rx.icon("play", size=16),
                        ),
                        rx.cond(
                            ExamState.is_loading_exams,
                            "載入中...",
                            "開始測驗",
                        ),
                        on_click=ExamState.start_exam,
                        disabled=ExamState.is_loading | ExamState.is_loading_exams,
                        size="3",
                        width="100%",
                        color_scheme="blue",
                    ),
                    spacing="5",
                    width="100%",
                ),
                width="500px",
                padding="6",
            ),
            padding="8",
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
