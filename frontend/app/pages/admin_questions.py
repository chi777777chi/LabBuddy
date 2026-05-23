import reflex as rx
from ..state.auth_state import AuthState
from ..state.admin_state import AdminState
from .admin import admin_nav_bar


YEAR_OPTIONS = [str(y) for y in range(114, 99, -1)]  # 114 → 100


def filter_bar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.text("科目：", size="2", color=rx.color("gray", 10)),
            rx.select.root(
                rx.select.trigger(placeholder="全部", width="180px"),
                rx.select.content(
                    rx.select.item("全部", value="all"),
                    rx.foreach(
                        AdminState.subjects,
                        lambda s: rx.select.item(s["name"], value=s["id"].to_string()),
                    ),
                ),
                on_change=AdminState.set_q_subject_filter,
            ),
            spacing="2",
            align="center",
        ),
        rx.hstack(
            rx.text("年份：", size="2", color=rx.color("gray", 10)),
            rx.select.root(
                rx.select.trigger(placeholder="全部", width="120px"),
                rx.select.content(
                    rx.select.item("全部", value="all"),
                    *[rx.select.item(f"{y} 年", value=y) for y in YEAR_OPTIONS],
                ),
                on_change=AdminState.set_q_year_filter,
            ),
            spacing="2",
            align="center",
        ),
        rx.spacer(),
        rx.button(
            rx.icon("plus", size=15),
            "新增題目",
            on_click=AdminState.open_add_dialog,
            color_scheme="blue",
            size="2",
        ),
        width="100%",
        align="center",
    )


def question_row(q) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    q["year"].to_string(), "-", q["sitting"].to_string(),
                    " 第 ", q["number"].to_string(), " 題",
                    color_scheme="blue",
                    variant="soft",
                ),
                rx.badge("答案：", q["answer"], color_scheme="green", variant="soft"),
                rx.cond(
                    q["difficulty"] != "",
                    rx.badge("難度：", q["difficulty"], color_scheme="orange", variant="soft"),
                    rx.fragment(),
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("pencil", size=14),
                    "編輯",
                    on_click=AdminState.open_edit_dialog(q["id"]),
                    size="1",
                    variant="soft",
                    color_scheme="blue",
                ),
                rx.button(
                    rx.icon("trash-2", size=14),
                    "刪除",
                    on_click=AdminState.confirm_delete(q["id"]),
                    size="1",
                    variant="soft",
                    color_scheme="red",
                ),
                width="100%",
                align="center",
                spacing="2",
            ),
            rx.text(q["content"], size="2", weight="medium"),
            rx.hstack(
                rx.text("A. ", q["option_a"], size="1", color=rx.color("gray", 11)),
                rx.text("B. ", q["option_b"], size="1", color=rx.color("gray", 11)),
                spacing="4",
            ),
            rx.hstack(
                rx.text("C. ", q["option_c"], size="1", color=rx.color("gray", 11)),
                rx.text("D. ", q["option_d"], size="1", color=rx.color("gray", 11)),
                spacing="4",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        width="100%",
        padding="3",
    )


def pagination_bar() -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.icon("chevron-left", size=15),
            "上一頁",
            on_click=AdminState.prev_page,
            disabled=AdminState.q_page <= 1,
            variant="soft",
            size="2",
        ),
        rx.text(AdminState.page_label, size="2", color=rx.color("gray", 10)),
        rx.button(
            "下一頁",
            rx.icon("chevron-right", size=15),
            on_click=AdminState.next_page,
            disabled=AdminState.q_page >= AdminState.total_pages,
            variant="soft",
            size="2",
        ),
        rx.hstack(
            rx.input(
                value=AdminState.jump_page_input,
                on_change=AdminState.set_jump_page_input,
                on_key_down=AdminState.handle_jump_key,
                placeholder="頁碼",
                type="number",
                min="1",
                width="70px",
                size="2",
            ),
            rx.button(
                "跳至",
                on_click=AdminState.jump_to_page,
                variant="soft",
                color_scheme="gray",
                size="2",
            ),
            spacing="1",
            align="center",
        ),
        spacing="3",
        align="center",
        justify="center",
        width="100%",
        padding_y="3",
    )


def q_form_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(AdminState.dialog_title),
            rx.dialog.description(
                "編輯題目資訊。標題列欄位（科目/年份/梯次/題號）僅在新增時可填。",
                size="1",
                color_scheme="gray",
            ),
            rx.vstack(
                # 第一列：科目/年份/梯次/題號（只在新增時顯示輸入框）
                rx.cond(
                    AdminState.edit_q_id == "",
                    rx.vstack(
                        rx.hstack(
                            rx.vstack(
                                rx.text("科目", size="1", weight="medium"),
                                rx.select.root(
                                    rx.select.trigger(placeholder="選擇科目", width="220px"),
                                    rx.select.content(
                                        rx.foreach(
                                            AdminState.subjects,
                                            lambda s: rx.select.item(s["name"], value=s["id"].to_string()),
                                        ),
                                    ),
                                    value=AdminState.form_subject_id,
                                    on_change=AdminState.set_form_subject_id,
                                ),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("年份", size="1", weight="medium"),
                                rx.input(
                                    value=AdminState.form_year,
                                    on_change=AdminState.set_form_year,
                                    placeholder="如 114",
                                    width="100px",
                                ),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("梯次", size="1", weight="medium"),
                                rx.select.root(
                                    rx.select.trigger(),
                                    rx.select.content(
                                        rx.select.item("第一次", value="1"),
                                        rx.select.item("第二次", value="2"),
                                    ),
                                    value=AdminState.form_sitting,
                                    on_change=AdminState.set_form_sitting,
                                ),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("題號", size="1", weight="medium"),
                                rx.input(
                                    value=AdminState.form_number,
                                    on_change=AdminState.set_form_number,
                                    placeholder="1-80",
                                    width="100px",
                                ),
                                spacing="1",
                            ),
                            spacing="3",
                            align="end",
                        ),
                        spacing="2",
                    ),
                    rx.fragment(),
                ),

                # 題目內容
                rx.vstack(
                    rx.text("題目內容", size="1", weight="medium"),
                    rx.text_area(
                        value=AdminState.form_content,
                        on_change=AdminState.set_form_content,
                        placeholder="輸入題幹⋯",
                        rows="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),

                # 選項 A/B
                rx.hstack(
                    rx.vstack(
                        rx.text("選項 A", size="1", weight="medium"),
                        rx.input(
                            value=AdminState.form_option_a,
                            on_change=AdminState.set_form_option_a,
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("選項 B", size="1", weight="medium"),
                        rx.input(
                            value=AdminState.form_option_b,
                            on_change=AdminState.set_form_option_b,
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # 選項 C/D
                rx.hstack(
                    rx.vstack(
                        rx.text("選項 C", size="1", weight="medium"),
                        rx.input(
                            value=AdminState.form_option_c,
                            on_change=AdminState.set_form_option_c,
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("選項 D", size="1", weight="medium"),
                        rx.input(
                            value=AdminState.form_option_d,
                            on_change=AdminState.set_form_option_d,
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # 正確答案
                rx.vstack(
                    rx.text("正確答案", size="1", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(),
                        rx.select.content(
                            rx.select.item("A", value="A"),
                            rx.select.item("B", value="B"),
                            rx.select.item("C", value="C"),
                            rx.select.item("D", value="D"),
                        ),
                        value=AdminState.form_answer,
                        on_change=AdminState.set_form_answer,
                    ),
                    spacing="1",
                ),

                # 錯誤訊息
                rx.cond(
                    AdminState.form_error != "",
                    rx.callout(
                        AdminState.form_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                    rx.fragment(),
                ),

                # 按鈕列
                rx.hstack(
                    rx.button(
                        "取消",
                        on_click=AdminState.close_q_dialog,
                        variant="soft",
                        color_scheme="gray",
                    ),
                    rx.button(
                        rx.icon("save", size=15),
                        "儲存",
                        on_click=AdminState.save_question,
                        color_scheme="blue",
                    ),
                    spacing="2",
                    justify="end",
                    width="100%",
                ),

                spacing="3",
                width="100%",
                padding_top="3",
            ),
            max_width="640px",
        ),
        open=AdminState.show_q_dialog,
        on_open_change=AdminState.set_q_dialog_open,
    )


def delete_confirm_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("確認刪除題目"),
            rx.dialog.description(
                "確定要刪除「", AdminState.delete_q_label, "」嗎？此操作無法復原。",
                size="2",
            ),
            rx.hstack(
                rx.button(
                    "取消",
                    on_click=AdminState.cancel_delete,
                    variant="soft",
                    color_scheme="gray",
                ),
                rx.button(
                    rx.icon("trash-2", size=15),
                    "確認刪除",
                    on_click=AdminState.do_delete,
                    color_scheme="red",
                ),
                spacing="2",
                justify="end",
                padding_top="3",
            ),
            max_width="420px",
        ),
        open=AdminState.show_delete_confirm,
        on_open_change=AdminState.set_delete_dialog_open,
    )


def flash_message() -> rx.Component:
    return rx.cond(
        AdminState.flash_msg != "",
        rx.callout(
            AdminState.flash_msg,
            icon="info",
            color_scheme=rx.cond(AdminState.flash_kind == "error", "red", "blue"),
            size="1",
        ),
        rx.fragment(),
    )


@rx.page(route="/admin/questions", on_load=[AuthState.load_user, AdminState.load_questions_page])
def admin_questions_page() -> rx.Component:
    return rx.box(
        admin_nav_bar(),
        rx.center(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=16),
                        "返回總覽",
                        on_click=rx.redirect("/admin"),
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                    ),
                    rx.heading("題庫管理", size="6"),
                    align="center",
                    spacing="4",
                ),
                flash_message(),
                filter_bar(),
                rx.cond(
                    AdminState.is_questions_loading,
                    rx.center(rx.spinner(size="3"), padding_y="8"),
                    rx.cond(
                        AdminState.questions.length() > 0,
                        rx.vstack(
                            rx.foreach(AdminState.questions, question_row),
                            pagination_bar(),
                            spacing="3",
                            width="100%",
                        ),
                        rx.center(
                            rx.text("沒有符合的題目", color=rx.color("gray", 8)),
                            padding_y="16",
                        ),
                    ),
                ),
                q_form_dialog(),
                delete_confirm_dialog(),
                width="960px",
                max_width="100%",
                spacing="4",
                padding="6",
            ),
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
