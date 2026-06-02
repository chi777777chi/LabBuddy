import reflex as rx
from ..state.auth_state import AuthState
from ..state.admin_state import AdminState
from .admin import admin_nav_bar


def admin_student_row(s: dict) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(s["name"], weight="medium", size="3"),
                rx.text(s["email"], size="1", color=rx.color("gray", 9)),
                spacing="0",
                align="start",
            ),
            rx.spacer(),
            rx.text(s["joined_at"], size="1", color=rx.color("gray", 9)),
            rx.button(
                rx.icon("user-x", size=14),
                "移除",
                on_click=AdminState.admin_remove_member(s["id"]),
                size="1",
                variant="soft",
                color_scheme="red",
            ),
            width="100%",
            align="center",
            spacing="3",
        ),
        padding="3",
        width="100%",
    )


@rx.page(
    route="/admin/classes/[class_id]",
    on_load=[AuthState.load_user, AdminState.load_admin_class_detail],
)
def admin_class_detail_page() -> rx.Component:
    return rx.box(
        admin_nav_bar(),
        rx.center(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=16),
                        "所有班級",
                        on_click=rx.call_script("window.location.href='/admin/classes'"),
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                    ),
                    rx.spacer(),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    AdminState.flash_msg != "",
                    rx.callout(
                        AdminState.flash_msg,
                        icon="info",
                        color_scheme=rx.cond(AdminState.flash_kind == "error", "red", "blue"),
                        size="1",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    AdminState.admin_class_loading,
                    rx.center(rx.spinner(size="3"), padding_y="8"),
                    rx.vstack(
                        # 班級資訊卡
                        rx.card(
                            rx.vstack(
                                rx.heading(AdminState.admin_current_class["name"], size="6"),
                                rx.hstack(
                                    rx.vstack(
                                        rx.text("授課老師", size="1", weight="medium", color=rx.color("gray", 10)),
                                        rx.text(AdminState.admin_current_class["teacher_name"], size="2"),
                                        rx.text(AdminState.admin_current_class["teacher_email"], size="1", color=rx.color("gray", 9)),
                                        spacing="1",
                                        align="start",
                                    ),
                                    rx.vstack(
                                        rx.text("邀請碼", size="1", weight="medium", color=rx.color("gray", 10)),
                                        rx.heading(
                                            AdminState.admin_current_class["invite_code"],
                                            size="5",
                                            color=rx.color("violet", 9),
                                            letter_spacing="4px",
                                        ),
                                        spacing="1",
                                        align="start",
                                    ),
                                    rx.vstack(
                                        rx.text("建立日期", size="1", weight="medium", color=rx.color("gray", 10)),
                                        rx.text(AdminState.admin_current_class["created_at"], size="2"),
                                        spacing="1",
                                        align="start",
                                    ),
                                    spacing="6",
                                    align="start",
                                    width="100%",
                                ),
                                spacing="3",
                                align="start",
                                width="100%",
                            ),
                            padding="5",
                            width="100%",
                        ),

                        # 加入學生
                        rx.card(
                            rx.vstack(
                                rx.hstack(
                                    rx.icon("user-plus", size=18, color=rx.color("green", 9)),
                                    rx.heading("手動加入學生", size="4"),
                                    spacing="2",
                                    align="center",
                                ),
                                rx.text(
                                    "輸入已註冊帳號的 email，即可將該使用者加入此班級。",
                                    size="1",
                                    color=rx.color("gray", 9),
                                ),
                                rx.hstack(
                                    rx.input(
                                        value=AdminState.admin_add_email,
                                        on_change=AdminState.set_admin_add_email,
                                        on_key_down=AdminState.handle_add_member_key,
                                        placeholder="student@example.com",
                                        width="100%",
                                    ),
                                    rx.button(
                                        rx.cond(
                                            AdminState.admin_add_loading,
                                            rx.spinner(size="2"),
                                            rx.icon("user-plus", size=15),
                                        ),
                                        "加入",
                                        on_click=AdminState.admin_add_member,
                                        disabled=AdminState.admin_add_loading,
                                        color_scheme="green",
                                        size="2",
                                    ),
                                    width="100%",
                                    spacing="2",
                                ),
                                rx.cond(
                                    AdminState.admin_add_error != "",
                                    rx.callout(
                                        AdminState.admin_add_error,
                                        icon="triangle-alert",
                                        color_scheme="red",
                                        size="1",
                                    ),
                                    rx.fragment(),
                                ),
                                spacing="3",
                                width="100%",
                                align="start",
                            ),
                            padding="5",
                            width="100%",
                        ),

                        # 學生名單
                        rx.vstack(
                            rx.hstack(
                                rx.heading("學生名單", size="4"),
                                rx.badge(
                                    AdminState.admin_class_students.length().to_string(),
                                    " 人",
                                    color_scheme="gray",
                                    variant="soft",
                                ),
                                spacing="2",
                                align="center",
                            ),
                            rx.cond(
                                AdminState.admin_class_students.length() > 0,
                                rx.vstack(
                                    rx.foreach(AdminState.admin_class_students, admin_student_row),
                                    spacing="2",
                                    width="100%",
                                ),
                                rx.center(
                                    rx.text("此班級尚無學生", color=rx.color("gray", 8)),
                                    padding_y="6",
                                ),
                            ),
                            spacing="3",
                            width="100%",
                        ),

                        spacing="4",
                        width="100%",
                    ),
                ),
                width="800px",
                max_width="100%",
                spacing="4",
                padding="6",
            ),
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
