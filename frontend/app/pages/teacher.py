import reflex as rx
from ..state.auth_state import AuthState
from ..state.teacher_state import TeacherState


def teacher_nav_bar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.icon("graduation-cap", size=18, color=rx.color("violet", 9)),
            rx.heading(
                "老師後台",
                size="4",
                on_click=rx.call_script("window.location.href='/teacher'"),
                cursor="pointer",
            ),
            spacing="2",
            align="center",
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(
                rx.icon("house", size=15),
                "回主選單",
                on_click=rx.call_script("window.location.href='/home'"),
                size="2",
                variant="ghost",
                color_scheme="blue",
            ),
            rx.avatar(src=AuthState.user_avatar, fallback=AuthState.user_name, size="2"),
            rx.text(AuthState.user_name, weight="medium"),
            rx.button(
                rx.icon("log-out", size=16),
                "登出",
                on_click=AuthState.logout,
                size="2",
                variant="ghost",
                color_scheme="gray",
            ),
            align="center",
            spacing="3",
        ),
        width="100%",
        padding_x="6",
        padding_y="4",
        border_bottom=f"1px solid {rx.color('gray', 4)}",
        background="white",
    )


def class_card(cls) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.heading(cls["name"], size="4"),
                    rx.badge(
                        cls["member_count"].to_string(), " 位學生",
                        color_scheme="violet",
                        variant="soft",
                    ),
                    spacing="3",
                    align="center",
                ),
                rx.hstack(
                    rx.text("邀請碼：", size="2", color=rx.color("gray", 10)),
                    rx.code(cls["invite_code"], size="2"),
                    spacing="1",
                    align="center",
                ),
                rx.text(cls["created_at"], size="1", color=rx.color("gray", 9)),
                spacing="2",
                align="start",
                flex="1",
                on_click=TeacherState.go_to_class(cls["id"]),
                cursor="pointer",
            ),
            rx.button(
                rx.icon("trash-2", size=15),
                on_click=TeacherState.open_delete_class_dialog(cls["id"], cls["name"]),
                size="2",
                variant="ghost",
                color_scheme="red",
            ),
            width="100%",
            align="center",
            spacing="3",
        ),
        _hover={"box_shadow": "0 4px 16px rgba(0,0,0,0.10)"},
        transition="box-shadow 0.2s",
        width="100%",
        padding="4",
    )


def delete_class_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("刪除班級"),
            rx.vstack(
                rx.text(
                    "確定要刪除「",
                    rx.text.span(TeacherState.delete_target_name, weight="bold"),
                    "」嗎？此操作無法復原，班級資料與成員紀錄將一併刪除。",
                    size="2",
                ),
                rx.hstack(
                    rx.button(
                        "取消",
                        on_click=TeacherState.close_delete_class_dialog,
                        variant="soft",
                        color_scheme="gray",
                    ),
                    rx.button(
                        rx.icon("trash-2", size=15),
                        "確認刪除",
                        on_click=TeacherState.confirm_delete_class,
                        color_scheme="red",
                    ),
                    spacing="2",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                padding_top="2",
            ),
            max_width="400px",
        ),
        open=TeacherState.show_delete_class_dialog,
        on_open_change=TeacherState.set_delete_class_dialog_open,
    )


def create_class_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("建立新班級"),
            rx.vstack(
                rx.vstack(
                    rx.text("班級名稱", size="1", weight="medium"),
                    rx.input(
                        value=TeacherState.new_class_name,
                        on_change=TeacherState.set_new_class_name,
                        placeholder="如：113學年度 甲班",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.cond(
                    TeacherState.create_error != "",
                    rx.callout(
                        TeacherState.create_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(
                        "取消",
                        on_click=TeacherState.close_create_dialog,
                        variant="soft",
                        color_scheme="gray",
                    ),
                    rx.button(
                        rx.icon("plus", size=15),
                        "建立",
                        on_click=TeacherState.create_class,
                        color_scheme="violet",
                    ),
                    spacing="2",
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                width="100%",
                padding_top="3",
            ),
            max_width="400px",
        ),
        open=TeacherState.show_create_dialog,
        on_open_change=TeacherState.set_create_dialog_open,
    )


@rx.page(route="/teacher", on_load=[AuthState.load_user, TeacherState.load_classes])
def teacher_page() -> rx.Component:
    return rx.box(
        teacher_nav_bar(),
        rx.center(
            rx.vstack(
                rx.hstack(
                    rx.heading("班級管理", size="6"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=15),
                        "建立班級",
                        on_click=TeacherState.open_create_dialog,
                        color_scheme="violet",
                        size="2",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    TeacherState.flash_msg != "",
                    rx.callout(
                        TeacherState.flash_msg,
                        icon="info",
                        color_scheme=rx.cond(TeacherState.flash_kind == "error", "red", "blue"),
                        size="1",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    TeacherState.is_classes_loading,
                    rx.center(rx.spinner(size="3"), padding_y="8"),
                    rx.cond(
                        TeacherState.classes.length() > 0,
                        rx.vstack(
                            rx.foreach(TeacherState.classes, class_card),
                            spacing="3",
                            width="100%",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("inbox", size=48, color=rx.color("gray", 6)),
                                rx.text(
                                    "還沒有班級，點右上角建立第一個班級",
                                    color=rx.color("gray", 8),
                                ),
                                align="center",
                                spacing="2",
                            ),
                            padding_y="16",
                        ),
                    ),
                ),
                create_class_dialog(),
                delete_class_dialog(),
                width="720px",
                max_width="100%",
                spacing="4",
                padding="6",
            ),
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
