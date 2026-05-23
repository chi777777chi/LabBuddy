import reflex as rx
from ..state.auth_state import AuthState
from ..state.admin_state import AdminState
from .admin import admin_nav_bar


def role_badge(role) -> rx.Component:
    return rx.badge(
        rx.match(
            role,
            ("student", "學生"),
            ("teacher", "老師"),
            ("admin", "管理員"),
            "未知",
        ),
        color_scheme=rx.match(
            role,
            ("student", "gray"),
            ("teacher", "violet"),
            ("admin", "red"),
            "gray",
        ),
        variant="soft",
        size="1",
    )


def role_button(user_id, label: str, role: str, color: str, current_role) -> rx.Component:
    is_current = current_role == role
    return rx.button(
        label,
        on_click=AdminState.update_role(user_id, role),
        size="1",
        variant=rx.cond(is_current, "solid", "soft"),
        color_scheme=color,
        disabled=is_current,
    )


def user_row(user) -> rx.Component:
    return rx.card(
        rx.hstack(
            # 左：使用者資訊
            rx.vstack(
                rx.hstack(
                    rx.text(user["name"], weight="bold", size="3"),
                    role_badge(user["role"]),
                    rx.cond(
                        user["is_active"],
                        rx.badge("啟用中", color_scheme="green", variant="soft", size="1"),
                        rx.badge("已停權", color_scheme="red", variant="soft", size="1"),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.text(user["email"], size="2", color=rx.color("gray", 10)),
                rx.text("加入：", user["created_at"], size="1", color=rx.color("gray", 9)),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            # 右：操作
            rx.vstack(
                rx.hstack(
                    role_button(user["id"], "學生", "student", "gray", user["role"]),
                    role_button(user["id"], "老師", "teacher", "violet", user["role"]),
                    role_button(user["id"], "管理員", "admin", "red", user["role"]),
                    spacing="1",
                ),
                rx.button(
                    rx.cond(user["is_active"], "停權", "解除停權"),
                    on_click=AdminState.toggle_ban(user["id"]),
                    color_scheme=rx.cond(user["is_active"], "red", "green"),
                    variant="soft",
                    size="1",
                ),
                spacing="2",
                align="end",
            ),
            width="100%",
            align="center",
        ),
        width="100%",
        padding="3",
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


@rx.page(route="/admin/users", on_load=[AuthState.load_user, AdminState.load_users])
def admin_users_page() -> rx.Component:
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
                    rx.heading("使用者管理", size="6"),
                    align="center",
                    spacing="4",
                ),
                rx.text(
                    "點按角色按鈕可立即變更使用者角色；停權後該帳號將被禁止存取管理員 API",
                    size="2",
                    color=rx.color("gray", 10),
                ),
                flash_message(),
                rx.cond(
                    AdminState.is_users_loading,
                    rx.center(rx.spinner(size="3"), padding_y="8"),
                    rx.vstack(
                        rx.foreach(AdminState.users, user_row),
                        spacing="3",
                        width="100%",
                    ),
                ),
                width="900px",
                max_width="100%",
                spacing="4",
                padding="6",
            ),
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
