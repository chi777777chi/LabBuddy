import httpx
import reflex as rx
from .auth_state import AuthState, BACKEND_URL


class AdminState(rx.State):
    # ── 統計 ──────────────────────────────────────────────────
    total_users: int = 0
    active_users: int = 0
    teacher_count: int = 0
    admin_count: int = 0
    total_sessions: int = 0
    total_answers: int = 0
    total_questions: int = 0
    subject_counts: list[dict] = []
    is_stats_loading: bool = False

    # ── 使用者列表 ────────────────────────────────────────────
    users: list[dict] = []
    is_users_loading: bool = False

    # ── 題庫列表 ──────────────────────────────────────────────
    questions: list[dict] = []
    total_q_count: int = 0
    q_page: int = 1
    q_page_size: int = 20
    q_subject_filter: int = 0   # 0 = all
    q_year_filter: int = 0      # 0 = all
    subjects: list[dict] = []
    is_questions_loading: bool = False

    # ── 新增/編輯題目 dialog ──────────────────────────────────
    show_q_dialog: bool = False
    edit_q_id: str = ""
    form_subject_id: str = "1"
    form_year: str = ""
    form_sitting: str = "1"
    form_number: str = ""
    form_content: str = ""
    form_option_a: str = ""
    form_option_b: str = ""
    form_option_c: str = ""
    form_option_d: str = ""
    form_answer: str = "A"
    form_error: str = ""

    # ── 刪除確認 dialog ───────────────────────────────────────
    show_delete_confirm: bool = False
    delete_q_id: str = ""
    delete_q_label: str = ""

    # ── 跳頁輸入 ──────────────────────────────────────────────
    jump_page_input: str = ""

    # ── 班級管理 ──────────────────────────────────────────────
    admin_classes: list[dict] = []
    admin_classes_loading: bool = False
    admin_current_class: dict = {}
    admin_class_students: list[dict] = []
    admin_class_loading: bool = False
    admin_add_email: str = ""
    admin_add_error: str = ""
    admin_add_loading: bool = False

    # ── 訊息 ──────────────────────────────────────────────────
    flash_msg: str = ""
    flash_kind: str = "info"   # info / error

    # ── computed ──────────────────────────────────────────────
    @rx.var
    def total_pages(self) -> int:
        if self.total_q_count == 0:
            return 1
        return (self.total_q_count + self.q_page_size - 1) // self.q_page_size

    @rx.var
    def page_label(self) -> str:
        return f"第 {self.q_page} / {self.total_pages} 頁，共 {self.total_q_count} 題"

    @rx.var
    def dialog_title(self) -> str:
        return "編輯題目" if self.edit_q_id else "新增題目"

    # ── 統計頁 ────────────────────────────────────────────────
    async def load_stats(self):
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        self.is_stats_loading = True
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/admin/stats",
                params={"token": auth.token},
            )
        self.is_stats_loading = False
        if resp.status_code == 403:
            return rx.redirect("/home")
        if resp.status_code == 200:
            data = resp.json()
            self.total_users = data["total_users"]
            self.active_users = data["active_users"]
            self.teacher_count = data["teacher_count"]
            self.admin_count = data["admin_count"]
            self.total_sessions = data["total_sessions"]
            self.total_answers = data["total_answers"]
            self.total_questions = data["total_questions"]
            self.subject_counts = data["subject_counts"]

    # ── 使用者列表 ────────────────────────────────────────────
    async def load_users(self):
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        self.is_users_loading = True
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/admin/users",
                params={"token": auth.token},
            )
        self.is_users_loading = False
        if resp.status_code == 403:
            return rx.redirect("/home")
        if resp.status_code == 200:
            self.users = resp.json()

    async def update_role(self, user_id: str, role: str):
        auth = await self.get_state(AuthState)
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{BACKEND_URL}/admin/users/{user_id}/role",
                params={"token": auth.token},
                json={"role": role},
            )
        if resp.status_code == 200:
            self.flash_msg = f"已更新角色為「{role}」"
            self.flash_kind = "info"
        else:
            self.flash_msg = resp.json().get("detail", "更新失敗")
            self.flash_kind = "error"
        await self.load_users()

    async def toggle_ban(self, user_id: str):
        auth = await self.get_state(AuthState)
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{BACKEND_URL}/admin/users/{user_id}/ban",
                params={"token": auth.token},
            )
        if resp.status_code == 200:
            self.flash_msg = "已更新狀態"
            self.flash_kind = "info"
        else:
            self.flash_msg = resp.json().get("detail", "更新失敗")
            self.flash_kind = "error"
        await self.load_users()

    # ── 題庫列表 ──────────────────────────────────────────────
    async def load_questions_page(self):
        """題庫頁 on_load：抓 subjects + questions"""
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        async with httpx.AsyncClient() as client:
            sresp = await client.get(f"{BACKEND_URL}/subjects/")
        if sresp.status_code == 200:
            self.subjects = [
                {"id": s["id"], "name": s["name"]}
                for s in sresp.json()
            ]
        await self.load_questions()

    async def load_questions(self):
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        self.is_questions_loading = True
        params = {
            "token": auth.token,
            "page": self.q_page,
            "page_size": self.q_page_size,
        }
        if self.q_subject_filter > 0:
            params["subject_id"] = self.q_subject_filter
        if self.q_year_filter > 0:
            params["year"] = self.q_year_filter
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/admin/questions",
                params=params,
            )
        self.is_questions_loading = False
        if resp.status_code == 403:
            return rx.redirect("/home")
        if resp.status_code == 200:
            data = resp.json()
            self.questions = data["questions"]
            self.total_q_count = data["total"]

    def set_q_subject_filter(self, val: str):
        self.q_subject_filter = int(val) if val and val != "all" else 0
        self.q_page = 1
        return AdminState.load_questions

    def set_q_year_filter(self, val: str):
        self.q_year_filter = int(val) if val and val != "all" else 0
        self.q_page = 1
        return AdminState.load_questions

    def prev_page(self):
        if self.q_page > 1:
            self.q_page -= 1
            return AdminState.load_questions

    def next_page(self):
        if self.q_page < self.total_pages:
            self.q_page += 1
            return AdminState.load_questions

    def set_jump_page_input(self, val: str):
        self.jump_page_input = val

    def jump_to_page(self):
        try:
            page = int(self.jump_page_input)
        except ValueError:
            return
        page = max(1, min(page, self.total_pages))
        self.q_page = page
        self.jump_page_input = ""
        return AdminState.load_questions

    def handle_jump_key(self, key: str):
        if key == "Enter":
            return AdminState.jump_to_page

    # ── form 欄位 setters（Reflex 0.9.x 不自動產生 set_*）──────
    def set_form_subject_id(self, val: str):
        self.form_subject_id = val

    def set_form_year(self, val: str):
        self.form_year = val

    def set_form_sitting(self, val: str):
        self.form_sitting = val

    def set_form_number(self, val: str):
        self.form_number = val

    def set_form_content(self, val: str):
        self.form_content = val

    def set_form_option_a(self, val: str):
        self.form_option_a = val

    def set_form_option_b(self, val: str):
        self.form_option_b = val

    def set_form_option_c(self, val: str):
        self.form_option_c = val

    def set_form_option_d(self, val: str):
        self.form_option_d = val

    def set_form_answer(self, val: str):
        self.form_answer = val

    # ── 新增/編輯題目 ─────────────────────────────────────────
    def open_add_dialog(self):
        self.show_q_dialog = True
        self.edit_q_id = ""
        self.form_subject_id = "1"
        self.form_year = ""
        self.form_sitting = "1"
        self.form_number = ""
        self.form_content = ""
        self.form_option_a = ""
        self.form_option_b = ""
        self.form_option_c = ""
        self.form_option_d = ""
        self.form_answer = "A"
        self.form_error = ""

    def open_edit_dialog(self, q_id: str):
        for q in self.questions:
            if q["id"] == q_id:
                self.show_q_dialog = True
                self.edit_q_id = q_id
                self.form_subject_id = str(q["subject_id"])
                self.form_year = str(q["year"])
                self.form_sitting = str(q["sitting"])
                self.form_number = str(q["number"])
                self.form_content = q["content"]
                self.form_option_a = q["option_a"]
                self.form_option_b = q["option_b"]
                self.form_option_c = q["option_c"]
                self.form_option_d = q["option_d"]
                self.form_answer = q["answer"]
                self.form_error = ""
                return

    def close_q_dialog(self):
        self.show_q_dialog = False
        self.edit_q_id = ""
        self.form_error = ""

    def set_q_dialog_open(self, is_open: bool):
        if not is_open:
            self.close_q_dialog()

    async def save_question(self):
        # 基本驗證
        if not self.form_content.strip():
            self.form_error = "題目內容不能為空"
            return
        for opt_name, opt_val in [
            ("選項 A", self.form_option_a),
            ("選項 B", self.form_option_b),
            ("選項 C", self.form_option_c),
            ("選項 D", self.form_option_d),
        ]:
            if not opt_val.strip():
                self.form_error = f"{opt_name} 不能為空"
                return
        if self.form_answer not in ("A", "B", "C", "D"):
            self.form_error = "正確答案必須為 A/B/C/D"
            return

        auth = await self.get_state(AuthState)
        body = {
            "content": self.form_content,
            "option_a": self.form_option_a,
            "option_b": self.form_option_b,
            "option_c": self.form_option_c,
            "option_d": self.form_option_d,
            "answer": self.form_answer,
        }
        async with httpx.AsyncClient() as client:
            if self.edit_q_id:
                resp = await client.patch(
                    f"{BACKEND_URL}/admin/questions/{self.edit_q_id}",
                    params={"token": auth.token},
                    json=body,
                )
            else:
                try:
                    body["subject_id"] = int(self.form_subject_id)
                    body["year"] = int(self.form_year)
                    body["sitting"] = int(self.form_sitting)
                    body["number"] = int(self.form_number)
                except ValueError:
                    self.form_error = "年份、梯次、題號必須是數字"
                    return
                resp = await client.post(
                    f"{BACKEND_URL}/admin/questions",
                    params={"token": auth.token},
                    json=body,
                )
        if resp.status_code in (200, 201):
            self.flash_msg = "題目已儲存"
            self.flash_kind = "info"
            self.close_q_dialog()
            await self.load_questions()
        else:
            self.form_error = resp.json().get("detail", "儲存失敗")

    # ── 刪除題目 ──────────────────────────────────────────────
    def confirm_delete(self, q_id: str):
        for q in self.questions:
            if q["id"] == q_id:
                self.delete_q_id = q_id
                self.delete_q_label = f"{q['year']}-{q['sitting']} 第 {q['number']} 題"
                self.show_delete_confirm = True
                return

    def cancel_delete(self):
        self.show_delete_confirm = False
        self.delete_q_id = ""
        self.delete_q_label = ""

    def set_delete_dialog_open(self, is_open: bool):
        if not is_open:
            self.cancel_delete()

    async def do_delete(self):
        auth = await self.get_state(AuthState)
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{BACKEND_URL}/admin/questions/{self.delete_q_id}",
                params={"token": auth.token},
            )
        if resp.status_code == 200:
            self.flash_msg = "題目已刪除"
            self.flash_kind = "info"
        else:
            self.flash_msg = "刪除失敗"
            self.flash_kind = "error"
        self.cancel_delete()
        await self.load_questions()

    # ── 班級管理 ──────────────────────────────────────────────
    def go_to_admin_class(self, class_id: str):
        return rx.redirect(f"/admin/classes/{class_id}")

    async def load_admin_classes(self):
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        self.admin_classes_loading = True
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/admin/classes",
                params={"token": auth.token},
            )
        self.admin_classes_loading = False
        if resp.status_code == 403:
            return rx.redirect("/home")
        if resp.status_code == 200:
            self.admin_classes = resp.json()

    async def load_admin_class_detail(self):
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        class_id = self.router.page.params.get("class_id", "")
        if not class_id:
            return rx.redirect("/admin/classes")
        self.admin_class_loading = True
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/admin/classes/{class_id}",
                params={"token": auth.token},
            )
        self.admin_class_loading = False
        if resp.status_code != 200:
            return rx.redirect("/admin/classes")
        data = resp.json()
        self.admin_current_class = {
            "id": data["id"],
            "name": data["name"],
            "invite_code": data["invite_code"],
            "teacher_name": data["teacher_name"],
            "teacher_email": data["teacher_email"],
            "created_at": data["created_at"],
        }
        self.admin_class_students = data["students"]
        self.admin_add_email = ""
        self.admin_add_error = ""

    def set_admin_add_email(self, val: str):
        self.admin_add_email = val
        self.admin_add_error = ""

    async def admin_add_member(self):
        if not self.admin_add_email.strip():
            self.admin_add_error = "請輸入 email"
            return
        auth = await self.get_state(AuthState)
        class_id = self.admin_current_class.get("id", "")
        self.admin_add_loading = True
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/admin/classes/{class_id}/members",
                params={"token": auth.token},
                json={"email": self.admin_add_email.strip()},
            )
        self.admin_add_loading = False
        if resp.status_code == 200:
            self.admin_add_email = ""
            self.admin_add_error = ""
            self.flash_msg = f"已加入「{resp.json()['name']}」"
            self.flash_kind = "info"
            await self.load_admin_class_detail()
        else:
            self.admin_add_error = resp.json().get("detail", "加入失敗")

    async def admin_remove_member(self, student_id: str):
        auth = await self.get_state(AuthState)
        class_id = self.admin_current_class.get("id", "")
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{BACKEND_URL}/admin/classes/{class_id}/members/{student_id}",
                params={"token": auth.token},
            )
        if resp.status_code == 200:
            self.admin_class_students = [
                s for s in self.admin_class_students if s["id"] != student_id
            ]
            self.flash_msg = "已將學生移出班級"
            self.flash_kind = "info"
        else:
            self.flash_msg = resp.json().get("detail", "移除失敗")
            self.flash_kind = "error"

    def handle_add_member_key(self, key: str):
        if key == "Enter":
            return AdminState.admin_add_member

    def clear_flash(self):
        self.flash_msg = ""
