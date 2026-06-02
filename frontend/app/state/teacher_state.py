import httpx
import reflex as rx
from .auth_state import AuthState, BACKEND_URL


class TeacherState(rx.State):
    # ── 班級列表 (/teacher) ────────────────────────────────────
    classes: list[dict] = []
    is_classes_loading: bool = False
    show_create_dialog: bool = False
    new_class_name: str = ""
    create_error: str = ""

    # ── 班級詳情 (/teacher/class/[class_id]) ──────────────────
    current_class: dict = {}
    class_students: list[dict] = []
    is_class_loading: bool = False

    # ── 學生進度 (/teacher/student/[student_id]) ──────────────
    viewed_student_name: str = ""
    viewed_student_email: str = ""
    viewed_class_name: str = ""
    student_sessions: list[dict] = []
    student_subject_stats: list[dict] = []
    is_student_loading: bool = False

    # ── 全班統計 (/teacher/stats/[class_id]) ──────────────────
    stats_class_name: str = ""
    stats_class_id: str = ""
    class_subject_stats: list[dict] = []
    top_wrong_questions: list[dict] = []
    is_stats_loading: bool = False

    # ── 刪除班級 ──────────────────────────────────────────────
    show_delete_class_dialog: bool = False
    delete_target_id: str = ""
    delete_target_name: str = ""

    # ── 改名班級 ──────────────────────────────────────────────
    show_rename_dialog: bool = False
    rename_input: str = ""
    rename_error: str = ""

    # ── 踢出學生 ──────────────────────────────────────────────
    show_remove_student_dialog: bool = False
    remove_student_id: str = ""
    remove_student_name: str = ""

    # ── 加入班級（學生端）────────────────────────────────────
    show_join_dialog: bool = False
    join_code_input: str = ""
    join_error: str = ""
    join_success: str = ""

    # ── 我的班級（學生端）────────────────────────────────────
    my_classes: list[dict] = []
    is_my_classes_loading: bool = False

    # ── 公告編輯（老師端）────────────────────────────────────
    announcements: list[dict] = []
    new_announcement_input: str = ""
    announcement_saving: bool = False

    # ── flash ──────────────────────────────────────────────────
    flash_msg: str = ""
    flash_kind: str = "info"

    # ── 班級列表 ──────────────────────────────────────────────
    async def load_classes(self):
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        self.is_classes_loading = True
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/teacher/classes",
                params={"token": auth.token},
            )
        self.is_classes_loading = False
        if resp.status_code == 403:
            return rx.redirect("/home")
        if resp.status_code == 200:
            self.classes = resp.json()

    def set_new_class_name(self, val: str):
        self.new_class_name = val

    def open_create_dialog(self):
        self.show_create_dialog = True
        self.new_class_name = ""
        self.create_error = ""

    def close_create_dialog(self):
        self.show_create_dialog = False
        self.new_class_name = ""
        self.create_error = ""

    def set_create_dialog_open(self, is_open: bool):
        if not is_open:
            self.close_create_dialog()

    async def create_class(self):
        if not self.new_class_name.strip():
            self.create_error = "班級名稱不能為空"
            return
        auth = await self.get_state(AuthState)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/teacher/classes",
                params={"token": auth.token},
                json={"name": self.new_class_name.strip()},
            )
        if resp.status_code == 200:
            self.close_create_dialog()
            self.flash_msg = "班級已建立"
            self.flash_kind = "info"
            await self.load_classes()
        else:
            self.create_error = resp.json().get("detail", "建立失敗")

    def go_to_class(self, class_id: str):
        return rx.redirect(f"/teacher/class/{class_id}")

    # ── 班級詳情 ──────────────────────────────────────────────
    async def load_class(self):
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        class_id = self.router.page.params.get("class_id", "")
        if not class_id:
            return rx.redirect("/teacher")
        self.is_class_loading = True
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/teacher/classes/{class_id}",
                params={"token": auth.token},
            )
        self.is_class_loading = False
        if resp.status_code in (403, 404):
            return rx.redirect("/teacher")
        if resp.status_code == 200:
            data = resp.json()
            self.current_class = {
                "id": data["id"],
                "name": data["name"],
                "invite_code": data["invite_code"],
                "created_at": data["created_at"],
            }
            self.announcements = data.get("announcements", [])
            self.new_announcement_input = ""
            self.class_students = data["students"]

    async def regenerate_code(self):
        auth = await self.get_state(AuthState)
        class_id = self.current_class.get("id", "")
        if not class_id:
            return
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/teacher/classes/{class_id}/regenerate-code",
                params={"token": auth.token},
            )
        if resp.status_code == 200:
            new_code = resp.json()["invite_code"]
            self.current_class = {**self.current_class, "invite_code": new_code}
            self.flash_msg = "邀請碼已更新"
            self.flash_kind = "info"

    def go_to_student(self, student_id: str):
        class_id = self.current_class.get("id", "")
        return rx.redirect(f"/teacher/student/{class_id}/{student_id}")

    def go_to_stats(self):
        class_id = self.current_class.get("id", "")
        if class_id:
            return rx.redirect(f"/teacher/stats/{class_id}")

    def back_to_class(self):
        class_id = self.router.page.params.get("class_id", "")
        return rx.redirect(f"/teacher/class/{class_id}")

    def back_from_stats(self):
        return rx.redirect(f"/teacher/class/{self.stats_class_id}")

    # ── 學生進度 ──────────────────────────────────────────────
    async def load_student_progress(self):
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        student_id = self.router.page.params.get("student_id", "")
        class_id = self.router.page.params.get("class_id", "")
        if not student_id or not class_id:
            return rx.redirect("/teacher")
        self.is_student_loading = True
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/teacher/classes/{class_id}/students/{student_id}",
                params={"token": auth.token},
            )
        self.is_student_loading = False
        if resp.status_code != 200:
            return rx.redirect("/teacher")
        data = resp.json()
        self.viewed_student_name = data["name"]
        self.viewed_student_email = data["email"]
        self.viewed_class_name = data["class_name"]
        self.student_sessions = data["sessions"]
        self.student_subject_stats = data["subject_stats"]

    # ── 全班統計 ──────────────────────────────────────────────
    async def load_class_stats(self):
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        class_id = self.router.page.params.get("class_id", "")
        if not class_id:
            return rx.redirect("/teacher")
        self.stats_class_id = class_id
        self.is_stats_loading = True
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/teacher/classes/{class_id}/stats",
                params={"token": auth.token},
            )
        self.is_stats_loading = False
        if resp.status_code != 200:
            return rx.redirect("/teacher")
        data = resp.json()
        self.stats_class_name = data["class_name"]
        self.class_subject_stats = [
            {**s, "score_color": "green" if s["avg_score"] >= 60 else "red"}
            for s in data["subject_stats"]
        ]
        self.top_wrong_questions = data["top_wrong_questions"]

    # ── 我的班級（學生端）────────────────────────────────────
    async def load_my_classes(self):
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        self.is_my_classes_loading = True
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/classes/mine",
                params={"token": auth.token},
            )
        self.is_my_classes_loading = False
        if resp.status_code == 200:
            self.my_classes = resp.json()

    # ── 公告編輯（老師端）────────────────────────────────────
    def set_new_announcement_input(self, val: str):
        self.new_announcement_input = val

    async def add_announcement(self):
        if not self.new_announcement_input.strip():
            return
        auth = await self.get_state(AuthState)
        class_id = self.current_class.get("id", "")
        if not class_id:
            return
        self.announcement_saving = True
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/teacher/classes/{class_id}/announcements",
                params={"token": auth.token},
                json={"content": self.new_announcement_input.strip()},
            )
        self.announcement_saving = False
        if resp.status_code == 200:
            self.announcements = [resp.json()] + self.announcements
            self.new_announcement_input = ""
            self.flash_msg = "公告已發布"
            self.flash_kind = "info"
        else:
            self.flash_msg = resp.json().get("detail", "發布失敗")
            self.flash_kind = "error"

    async def delete_announcement(self, ann_id: str):
        auth = await self.get_state(AuthState)
        class_id = self.current_class.get("id", "")
        if not class_id:
            return
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{BACKEND_URL}/teacher/classes/{class_id}/announcements/{ann_id}",
                params={"token": auth.token},
            )
        if resp.status_code == 200:
            self.announcements = [a for a in self.announcements if a["id"] != ann_id]
            self.flash_msg = "公告已刪除"
            self.flash_kind = "info"
        else:
            self.flash_msg = resp.json().get("detail", "刪除失敗")
            self.flash_kind = "error"

    # ── 加入班級（學生端）────────────────────────────────────
    def set_join_code_input(self, val: str):
        self.join_code_input = val

    def open_join_dialog(self):
        self.show_join_dialog = True
        self.join_code_input = ""
        self.join_error = ""
        self.join_success = ""

    def close_join_dialog(self):
        self.show_join_dialog = False

    def set_join_dialog_open(self, is_open: bool):
        if not is_open:
            self.close_join_dialog()

    async def join_class(self):
        if not self.join_code_input.strip():
            self.join_error = "請輸入邀請碼"
            return
        auth = await self.get_state(AuthState)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/classes/join",
                params={"token": auth.token},
                json={"invite_code": self.join_code_input.strip()},
            )
        if resp.status_code == 200:
            class_name = resp.json()["class_name"]
            self.join_success = f"成功加入「{class_name}」！"
            self.join_error = ""
            self.join_code_input = ""
        else:
            self.join_error = resp.json().get("detail", "加入失敗")
            self.join_success = ""

    def handle_join_key(self, key: str):
        if key == "Enter":
            return TeacherState.join_class

    # ── 刪除班級 ──────────────────────────────────────────────
    def open_delete_class_dialog(self, class_id: str, class_name: str):
        self.delete_target_id = class_id
        self.delete_target_name = class_name
        self.show_delete_class_dialog = True

    def close_delete_class_dialog(self):
        self.show_delete_class_dialog = False
        self.delete_target_id = ""
        self.delete_target_name = ""

    def set_delete_class_dialog_open(self, is_open: bool):
        if not is_open:
            self.close_delete_class_dialog()

    async def confirm_delete_class(self):
        auth = await self.get_state(AuthState)
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{BACKEND_URL}/teacher/classes/{self.delete_target_id}",
                params={"token": auth.token},
            )
        self.close_delete_class_dialog()
        if resp.status_code == 200:
            self.flash_msg = f"已刪除班級「{self.delete_target_name}」"
            self.flash_kind = "info"
            await self.load_classes()
        else:
            self.flash_msg = resp.json().get("detail", "刪除失敗")
            self.flash_kind = "error"

    # ── 改名班級 ──────────────────────────────────────────────
    def open_rename_dialog(self):
        self.rename_input = self.current_class.get("name", "")
        self.rename_error = ""
        self.show_rename_dialog = True

    def close_rename_dialog(self):
        self.show_rename_dialog = False
        self.rename_input = ""
        self.rename_error = ""

    def set_rename_dialog_open(self, is_open: bool):
        if not is_open:
            self.close_rename_dialog()

    def set_rename_input(self, val: str):
        self.rename_input = val

    async def rename_class(self):
        if not self.rename_input.strip():
            self.rename_error = "班級名稱不能為空"
            return
        auth = await self.get_state(AuthState)
        class_id = self.current_class.get("id", "")
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{BACKEND_URL}/teacher/classes/{class_id}",
                params={"token": auth.token},
                json={"name": self.rename_input.strip()},
            )
        if resp.status_code == 200:
            new_name = resp.json()["name"]
            self.current_class = {**self.current_class, "name": new_name}
            self.close_rename_dialog()
            self.flash_msg = "班級名稱已更新"
            self.flash_kind = "info"
        else:
            self.rename_error = resp.json().get("detail", "更新失敗")

    # ── 踢出學生 ──────────────────────────────────────────────
    def open_remove_student_dialog(self, student_id: str, student_name: str):
        self.remove_student_id = student_id
        self.remove_student_name = student_name
        self.show_remove_student_dialog = True

    def close_remove_student_dialog(self):
        self.show_remove_student_dialog = False
        self.remove_student_id = ""
        self.remove_student_name = ""

    def set_remove_student_dialog_open(self, is_open: bool):
        if not is_open:
            self.close_remove_student_dialog()

    async def confirm_remove_student(self):
        auth = await self.get_state(AuthState)
        class_id = self.current_class.get("id", "")
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{BACKEND_URL}/teacher/classes/{class_id}/members/{self.remove_student_id}",
                params={"token": auth.token},
            )
        self.close_remove_student_dialog()
        if resp.status_code == 200:
            self.flash_msg = f"已將「{self.remove_student_name}」移出班級"
            self.flash_kind = "info"
            await self.load_class()
        else:
            self.flash_msg = resp.json().get("detail", "移除失敗")
            self.flash_kind = "error"

    def clear_flash(self):
        self.flash_msg = ""
