import reflex as rx
from ..state.auth_state import AuthState
from ..state.teacher_state import TeacherState
from .teacher import teacher_nav_bar


def student_row(s) -> rx.Component:
    return rx.card(
        rx.hstack(
            # 可點擊區域（整列，不含移除按鈕）
            rx.hstack(
                rx.vstack(
                    rx.text(s["name"], weight="medium", size="3"),
                    rx.text(s["email"], size="1", color=rx.color("gray", 9)),
                    spacing="0",
                    align="start",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text("最近作答：", s["last_attempt"], size="1", color=rx.color("gray", 9)),
                    rx.text("測驗場次：", s["total_sessions"].to_string(), " 場", size="1", color=rx.color("gray", 9)),
                    spacing="0",
                    align="end",
                ),
                rx.cond(
                    s["avg_score"] != "",
                    rx.badge(s["avg_score"], "%", color_scheme="green", variant="soft"),
                    rx.badge("尚無紀錄", color_scheme="gray", variant="soft"),
                ),
                rx.icon("chevron-right", size=15, color=rx.color("gray", 9)),
                on_click=TeacherState.go_to_student(s["id"]),
                cursor="pointer",
                flex="1",
                align="center",
                spacing="3",
            ),
            # 移除按鈕獨立，不觸發導覽
            rx.button(
                rx.icon("user-x", size=15),
                on_click=TeacherState.open_remove_student_dialog(s["id"], s["name"]),
                size="1",
                variant="ghost",
                color_scheme="red",
            ),
            width="100%",
            align="center",
            spacing="2",
        ),
        width="100%",
        padding="3",
    )


def rename_class_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("修改班級名稱"),
            rx.vstack(
                rx.vstack(
                    rx.text("新名稱", size="1", weight="medium"),
                    rx.input(
                        value=TeacherState.rename_input,
                        on_change=TeacherState.set_rename_input,
                        placeholder="輸入新班級名稱",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.cond(
                    TeacherState.rename_error != "",
                    rx.callout(
                        TeacherState.rename_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(
                        "取消",
                        on_click=TeacherState.close_rename_dialog,
                        variant="soft",
                        color_scheme="gray",
                    ),
                    rx.button(
                        rx.icon("pencil", size=15),
                        "儲存",
                        on_click=TeacherState.rename_class,
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
        open=TeacherState.show_rename_dialog,
        on_open_change=TeacherState.set_rename_dialog_open,
    )


def remove_student_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("移出學生"),
            rx.vstack(
                rx.text(
                    "確定要將「",
                    rx.text.span(TeacherState.remove_student_name, weight="bold"),
                    "」從班級中移除嗎？",
                    size="2",
                ),
                rx.hstack(
                    rx.button(
                        "取消",
                        on_click=TeacherState.close_remove_student_dialog,
                        variant="soft",
                        color_scheme="gray",
                    ),
                    rx.button(
                        rx.icon("user-x", size=15),
                        "確認移除",
                        on_click=TeacherState.confirm_remove_student,
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
        open=TeacherState.show_remove_student_dialog,
        on_open_change=TeacherState.set_remove_student_dialog_open,
    )


@rx.page(route="/teacher/class/[class_id]", on_load=[AuthState.load_user, TeacherState.load_class])
def teacher_class_page() -> rx.Component:
    return rx.box(
        teacher_nav_bar(),
        rx.center(
            rx.vstack(
                rx.hstack(
                    rx.button(
                        rx.icon("arrow-left", size=16),
                        "班級列表",
                        on_click=rx.call_script("window.location.href='/teacher'"),
                        variant="ghost",
                        color_scheme="gray",
                        size="2",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("bar-chart-2", size=15),
                        "全班統計",
                        on_click=TeacherState.go_to_stats,
                        variant="soft",
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
                    TeacherState.is_class_loading,
                    rx.center(rx.spinner(size="3"), padding_y="8"),
                    rx.vstack(
                        # 班級資訊卡
                        rx.card(
                            rx.vstack(
                                rx.hstack(
                                    rx.heading(TeacherState.current_class["name"], size="6"),
                                    rx.button(
                                        rx.icon("pencil", size=14),
                                        on_click=TeacherState.open_rename_dialog,
                                        size="1",
                                        variant="ghost",
                                        color_scheme="gray",
                                    ),
                                    spacing="2",
                                    align="center",
                                ),
                                rx.text(
                                    "建立於 ", TeacherState.current_class["created_at"],
                                    size="2",
                                    color=rx.color("gray", 9),
                                ),
                                rx.hstack(
                                    rx.vstack(
                                        rx.text("邀請碼", size="1", weight="medium", color=rx.color("gray", 10)),
                                        rx.hstack(
                                            rx.heading(
                                                TeacherState.current_class["invite_code"],
                                                size="7",
                                                color=rx.color("violet", 9),
                                                letter_spacing="6px",
                                            ),
                                            rx.button(
                                                rx.icon("refresh-cw", size=14),
                                                "重新產生",
                                                on_click=TeacherState.regenerate_code,
                                                size="1",
                                                variant="soft",
                                                color_scheme="orange",
                                            ),
                                            spacing="3",
                                            align="center",
                                        ),
                                        rx.text(
                                            "請將此 6 碼邀請碼提供給學生，讓他們在主選單「加入班級」輸入",
                                            size="1",
                                            color=rx.color("gray", 9),
                                        ),
                                        spacing="1",
                                        align="start",
                                    ),
                                    spacing="4",
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

                        # 公告區
                        rx.card(
                            rx.vstack(
                                rx.hstack(
                                    rx.icon("megaphone", size=18, color=rx.color("orange", 9)),
                                    rx.heading("班級公告", size="4"),
                                    rx.badge(
                                        TeacherState.announcements.length().to_string(),
                                        " 則",
                                        color_scheme="orange",
                                        variant="soft",
                                    ),
                                    spacing="2",
                                    align="center",
                                ),
                                # 新增公告輸入
                                rx.vstack(
                                    rx.text_area(
                                        value=TeacherState.new_announcement_input,
                                        on_change=TeacherState.set_new_announcement_input,
                                        placeholder="輸入新公告內容...",
                                        rows="3",
                                        width="100%",
                                    ),
                                    rx.hstack(
                                        rx.button(
                                            rx.cond(
                                                TeacherState.announcement_saving,
                                                rx.spinner(size="2"),
                                                rx.icon("send", size=15),
                                            ),
                                            "發布公告",
                                            on_click=TeacherState.add_announcement,
                                            disabled=TeacherState.announcement_saving,
                                            color_scheme="orange",
                                            size="2",
                                        ),
                                        justify="end",
                                        width="100%",
                                    ),
                                    spacing="2",
                                    width="100%",
                                ),
                                # 已發布公告列表
                                rx.cond(
                                    TeacherState.announcements.length() > 0,
                                    rx.vstack(
                                        rx.divider(),
                                        rx.foreach(
                                            TeacherState.announcements,
                                            lambda ann: rx.card(
                                                rx.hstack(
                                                    rx.vstack(
                                                        rx.text(ann["content"], size="2", white_space="pre-wrap"),
                                                        rx.text(ann["created_at"], size="1", color=rx.color("gray", 9)),
                                                        spacing="1",
                                                        align="start",
                                                        width="100%",
                                                    ),
                                                    rx.button(
                                                        rx.icon("trash-2", size=14),
                                                        on_click=TeacherState.delete_announcement(ann["id"]),
                                                        size="1",
                                                        variant="ghost",
                                                        color_scheme="red",
                                                    ),
                                                    align="start",
                                                    width="100%",
                                                ),
                                                padding="3",
                                                width="100%",
                                                variant="surface",
                                            ),
                                        ),
                                        spacing="2",
                                        width="100%",
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
                                    TeacherState.class_students.length().to_string(),
                                    " 人",
                                    color_scheme="gray",
                                    variant="soft",
                                ),
                                spacing="2",
                                align="center",
                            ),
                            rx.cond(
                                TeacherState.class_students.length() > 0,
                                rx.vstack(
                                    rx.foreach(TeacherState.class_students, student_row),
                                    spacing="2",
                                    width="100%",
                                ),
                                rx.center(
                                    rx.text("尚無學生加入，分享邀請碼給學生", color=rx.color("gray", 8)),
                                    padding_y="8",
                                ),
                            ),
                            spacing="3",
                            width="100%",
                        ),

                        rename_class_dialog(),
                        remove_student_dialog(),
                        spacing="4",
                        width="100%",
                    ),
                ),
                width="760px",
                max_width="100%",
                spacing="4",
                padding="6",
            ),
        ),
        min_height="100vh",
        background=rx.color("gray", 2),
    )
