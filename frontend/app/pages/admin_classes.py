import reflex as rx
from ..state.auth_state import AuthState
from ..state.admin_state import AdminState
from .admin import admin_nav_bar


def admin_create_class_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("建立新班級"),
            rx.vstack(
                rx.vstack(
                    rx.text("班級名稱", size="1", weight="medium"),
                    rx.input(
                        value=AdminState.admin_new_class_name,
                        on_change=AdminState.set_admin_new_class_name,
                        placeholder="如：113學年度 甲班",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.cond(
                    AdminState.admin_create_error != "",
                    rx.callout(
                        AdminState.admin_create_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(
                        "取消",
                        on_click=AdminState.close_admin_create_dialog,
                        variant="soft",
                        color_scheme="gray",
                    ),
                    rx.button(
                        rx.icon("plus", size=15),
                        "建立",
                        on_click=AdminState.admin_create_class,
                        color_scheme="green",
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
        open=AdminState.show_admin_create_dialog,
        on_open_change=AdminState.set_admin_create_dialog_open,
    )


def class_row(cls: dict) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(cls["name"], weight="bold", size="3"),
                rx.text(
                    "授課老師：", cls["teacher_name"],
                    size="1",
                    color=rx.color("gray", 9),
                ),
                rx.text(
                    cls["teacher_email"],
                    size="1",
                    color=rx.color("gray", 9),
                ),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.vstack(
                rx.badge(cls["member_count"].to_string(), " 人", color_scheme="blue", variant="soft"),
                rx.text(cls["created_at"], size="1", color=rx.color("gray", 9)),
                spacing="1",
                align="end",
            ),
            rx.icon("chevron-right", size=15, color=rx.color("gray", 9)),
            width="100%",
            align="center",
            spacing="3",
        ),
        width="100%",
        padding="3",
        cursor="pointer",
        on_click=AdminState.go_to_admin_class(cls["id"]),
        _hover={"box_shadow": "0 2px 8px rgba(0,0,0,0.08)"},
    )


@rx.page(route="/admin/classes", on_load=[AuthState.load_user, AdminState.load_admin_classes])
def admin_classes_page() -> rx.Component:
    return rx.box(
        admin_nav_bar(),
        rx.center(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=16),
                        "管理員總覽",
                        on_click=rx.call_script("window.location.href='/admin'"),
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                    ),
                    rx.spacer(),
                    width="100%",
                    align="center",
                ),
                rx.hstack(
                    rx.hstack(
                        rx.icon("school", size=22, color=rx.color("green", 9)),
                        rx.heading("班級管理", size="6"),
                        spacing="2",
                        align="center",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=15),
                        "建立班級",
                        on_click=AdminState.open_admin_create_dialog,
                        color_scheme="green",
                        size="2",
                    ),
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
                admin_create_class_dialog(),
                rx.cond(
                    AdminState.admin_classes_loading,
                    rx.center(rx.spinner(size="3"), padding_y="8"),
                    rx.vstack(
                        rx.text(
                            "共 ",
                            AdminState.admin_classes.length().to_string(),
                            " 個班級",
                            size="2",
                            color=rx.color("gray", 9),
                        ),
                        rx.cond(
                            AdminState.admin_classes.length() > 0,
                            rx.vstack(
                                rx.foreach(AdminState.admin_classes, class_row),
                                spacing="2",
                                width="100%",
                            ),
                            rx.center(
                                rx.text("目前沒有任何班級", color=rx.color("gray", 8)),
                                padding_y="8",
                            ),
                        ),
                        spacing="3",
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
