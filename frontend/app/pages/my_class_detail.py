import reflex as rx
from ..state.auth_state import AuthState
from ..state.teacher_state import TeacherState
from .home import nav_bar


def member_row(m: dict) -> rx.Component:
    return rx.hstack(
        rx.icon("user-circle", size=28, color=rx.color("violet", 8)),
        rx.vstack(
            rx.text(m["name"], size="2", weight="medium"),
            rx.text("加入於 ", m["joined_at"], size="1", color=rx.color("gray", 8)),
            spacing="0",
            align="start",
        ),
        spacing="3",
        align="center",
        width="100%",
        padding_y="2",
    )


def announcement_block(ann: dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(ann["content"], size="2", line_height="1.7", white_space="pre-wrap"),
            rx.text(ann["created_at"], size="1", color=rx.color("gray", 8)),
            spacing="1",
            align="start",
            width="100%",
        ),
        padding="3",
        border_radius="8px",
        border=f"1px solid {rx.color('orange', 4)}",
        background=rx.color("orange", 2),
        width="100%",
    )


@rx.page(
    route="/my-class/[class_id]",
    on_load=[AuthState.load_user, TeacherState.load_my_class_detail],
)
def my_class_detail_page() -> rx.Component:
    return rx.box(
        nav_bar(),
        rx.center(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=16),
                        "我的班級",
                        on_click=rx.call_script("window.location.href='/my-class'"),
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                    ),
                    rx.spacer(),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    TeacherState.is_my_class_detail_loading,
                    rx.center(rx.spinner(size="3"), padding_y="8"),
                    rx.vstack(
                        # 班級標題
                        rx.hstack(
                            rx.icon("graduation-cap", size=22, color=rx.color("violet", 9)),
                            rx.heading(TeacherState.my_class_detail["name"], size="6"),
                            spacing="2",
                            align="center",
                        ),
                        rx.hstack(
                            rx.icon("user", size=14, color=rx.color("gray", 9)),
                            rx.text(
                                "授課老師：",
                                TeacherState.my_class_detail["teacher_name"],
                                size="2",
                                color=rx.color("gray", 10),
                            ),
                            rx.spacer(),
                            rx.icon("users", size=14, color=rx.color("gray", 9)),
                            rx.text(
                                TeacherState.my_class_detail["member_count"].to_string(),
                                " 人",
                                size="2",
                                color=rx.color("gray", 10),
                            ),
                            width="100%",
                            align="center",
                        ),

                        # 公告區
                        rx.cond(
                            TeacherState.my_class_announcements.length() > 0,
                            rx.card(
                                rx.vstack(
                                    rx.hstack(
                                        rx.icon("megaphone", size=16, color=rx.color("orange", 9)),
                                        rx.heading("老師公告", size="4", color=rx.color("orange", 9)),
                                        rx.badge(
                                            TeacherState.my_class_announcements.length().to_string(),
                                            " 則",
                                            color_scheme="orange",
                                            variant="soft",
                                        ),
                                        spacing="2",
                                        align="center",
                                    ),
                                    rx.foreach(
                                        TeacherState.my_class_announcements,
                                        announcement_block,
                                    ),
                                    spacing="3",
                                    width="100%",
                                    align="start",
                                ),
                                padding="5",
                                width="100%",
                            ),
                            rx.fragment(),
                        ),

                        # 同學名單
                        rx.card(
                            rx.vstack(
                                rx.hstack(
                                    rx.icon("users", size=16, color=rx.color("violet", 9)),
                                    rx.heading("同學名單", size="4"),
                                    rx.badge(
                                        TeacherState.my_class_members.length().to_string(),
                                        " 人",
                                        color_scheme="violet",
                                        variant="soft",
                                    ),
                                    spacing="2",
                                    align="center",
                                ),
                                rx.divider(),
                                rx.cond(
                                    TeacherState.my_class_members.length() > 0,
                                    rx.vstack(
                                        rx.foreach(TeacherState.my_class_members, member_row),
                                        spacing="1",
                                        width="100%",
                                    ),
                                    rx.center(
                                        rx.text("班級中尚無其他成員", color=rx.color("gray", 7)),
                                        padding_y="4",
                                    ),
                                ),
                                spacing="3",
                                width="100%",
                                align="start",
                            ),
                            padding="5",
                            width="100%",
                        ),

                        spacing="4",
                        width="100%",
                    ),
                ),
                width="640px",
                max_width="100%",
                spacing="5",
                padding="6",
            ),
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
