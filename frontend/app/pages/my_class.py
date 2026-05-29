import reflex as rx
from ..state.auth_state import AuthState
from ..state.teacher_state import TeacherState
from .home import nav_bar, join_class_dialog


def class_card(cls) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("graduation-cap", size=20, color=rx.color("violet", 9)),
                rx.text(cls["name"], size="4", weight="bold"),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.icon("user", size=13, color=rx.color("gray", 9)),
                rx.text("老師：", cls["teacher_name"], size="2", color=rx.color("gray", 10)),
                rx.spacer(),
                rx.icon("users", size=13, color=rx.color("gray", 9)),
                rx.text(cls["member_count"].to_string(), " 人", size="2", color=rx.color("gray", 10)),
                align="center",
                width="100%",
            ),
            rx.text(
                "加入於 ", cls["joined_at"],
                size="1",
                color=rx.color("gray", 8),
            ),
            rx.cond(
                cls["announcement"] != "",
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("megaphone", size=14, color=rx.color("orange", 9)),
                            rx.text("老師公告", size="2", weight="bold", color=rx.color("orange", 9)),
                            spacing="2",
                            align="center",
                        ),
                        rx.text(
                            cls["announcement"],
                            size="2",
                            line_height="1.7",
                            white_space="pre-wrap",
                        ),
                        spacing="2",
                        align="start",
                        width="100%",
                    ),
                    background=rx.color("orange", 2),
                    border=f"1px solid {rx.color('orange', 4)}",
                    border_radius="8px",
                    padding="3",
                    width="100%",
                ),
                rx.text("（尚無公告）", size="2", color=rx.color("gray", 7), font_style="italic"),
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
        padding="5",
    )


@rx.page(route="/my-class", on_load=[AuthState.load_user, TeacherState.load_my_classes])
def my_class_page() -> rx.Component:
    return rx.box(
        nav_bar(),
        join_class_dialog(),
        rx.center(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=16),
                        "返回主選單",
                        on_click=rx.call_script("window.location.href='/home'"),
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=15),
                        "加入新班級",
                        on_click=TeacherState.open_join_dialog,
                        color_scheme="blue",
                        size="2",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.heading("我的班級", size="5"),
                rx.cond(
                    TeacherState.is_my_classes_loading,
                    rx.center(rx.spinner(size="3"), padding_y="8", width="100%"),
                    rx.cond(
                        TeacherState.my_classes.length() > 0,
                        rx.vstack(
                            rx.foreach(TeacherState.my_classes, class_card),
                            spacing="4",
                            width="100%",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("school", size=48, color=rx.color("gray", 5)),
                                rx.text("尚未加入任何班級", size="3", color=rx.color("gray", 8)),
                                rx.text(
                                    "請向老師索取邀請碼，點擊右上角「加入新班級」",
                                    size="2",
                                    color=rx.color("gray", 7),
                                ),
                                rx.button(
                                    rx.icon("plus", size=15),
                                    "加入班級",
                                    on_click=TeacherState.open_join_dialog,
                                    color_scheme="blue",
                                    size="3",
                                    margin_top="4",
                                ),
                                spacing="2",
                                align="center",
                            ),
                            padding_y="12",
                            width="100%",
                        ),
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
