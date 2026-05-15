import httpx
import reflex as rx
from pydantic import BaseModel
from .auth_state import AuthState, BACKEND_URL


class ResultDetail(BaseModel):
    order: int = 0
    content: str = ""
    chosen: str = ""
    correct_answer: str = ""
    is_correct: bool = False
    is_unanswered: bool = False


class ExamState(rx.State):
    # ── 設定頁 ────────────────────────────────────────────────
    subjects: list[dict] = []
    selected_subject_id: int = 1
    selected_mode: str = "single_full"
    selected_count: int = 10
    selected_year: int = 114
    selected_sitting: int = 2
    shuffle_options: bool = False
    timed: bool = False
    instant_review: bool = True
    save_to_history: bool = True
    available_exams: list[dict] = []

    # ── 考試中 ────────────────────────────────────────────────
    session_id: str = ""
    questions: list[dict] = []
    current_index: int = 0
    selected_answers: dict[str, str] = {}
    eliminated: dict[str, list] = {}
    feedback: dict[str, dict] = {}
    answered_via_api: dict[str, bool] = {}
    is_loading: bool = False
    error_msg: str = ""

    # ── 計時器 ────────────────────────────────────────────────
    time_left: int = 0
    is_timer_running: bool = False

    # ── 成績 ─────────────────────────────────────────────────
    result_score: int = 0
    result_total: int = 0
    result_percentage: float = 0.0
    result_details: list[ResultDetail] = []

    # ── 基本 computed vars ────────────────────────────────────
    @rx.var
    def total_questions(self) -> int:
        return len(self.questions)

    @rx.var
    def progress_text(self) -> str:
        return f"{self.current_index + 1} / {len(self.questions)}"

    @rx.var
    def is_last_question(self) -> bool:
        return self.current_index >= len(self.questions) - 1

    @rx.var
    def has_session(self) -> bool:
        return self.session_id != ""

    @rx.var
    def current_qid(self) -> str:
        if not self.questions or self.current_index >= len(self.questions):
            return ""
        return self.questions[self.current_index].get("question_id", "")

    @rx.var
    def time_display(self) -> str:
        mins = self.time_left // 60
        secs = self.time_left % 60
        return f"{mins:02d}:{secs:02d}"

    # ── 題目內容 computed vars ────────────────────────────────
    @rx.var
    def current_content(self) -> str:
        if not self.questions or self.current_index >= len(self.questions):
            return ""
        return self.questions[self.current_index].get("content", "")

    @rx.var
    def current_source(self) -> str:
        if not self.questions or self.current_index >= len(self.questions):
            return ""
        return self.questions[self.current_index].get("source", "")

    @rx.var
    def option_a_text(self) -> str:
        if not self.questions or self.current_index >= len(self.questions):
            return ""
        return self.questions[self.current_index].get("options", {}).get("A", "")

    @rx.var
    def option_b_text(self) -> str:
        if not self.questions or self.current_index >= len(self.questions):
            return ""
        return self.questions[self.current_index].get("options", {}).get("B", "")

    @rx.var
    def option_c_text(self) -> str:
        if not self.questions or self.current_index >= len(self.questions):
            return ""
        return self.questions[self.current_index].get("options", {}).get("C", "")

    @rx.var
    def option_d_text(self) -> str:
        if not self.questions or self.current_index >= len(self.questions):
            return ""
        return self.questions[self.current_index].get("options", {}).get("D", "")

    # ── 選擇狀態 computed vars ────────────────────────────────
    @rx.var
    def selected_a(self) -> bool:
        return self.selected_answers.get(self.current_qid, "") == "A"

    @rx.var
    def selected_b(self) -> bool:
        return self.selected_answers.get(self.current_qid, "") == "B"

    @rx.var
    def selected_c(self) -> bool:
        return self.selected_answers.get(self.current_qid, "") == "C"

    @rx.var
    def selected_d(self) -> bool:
        return self.selected_answers.get(self.current_qid, "") == "D"

    # ── 刪去狀態 computed vars ────────────────────────────────
    @rx.var
    def eliminated_a(self) -> bool:
        return "A" in self.eliminated.get(self.current_qid, [])

    @rx.var
    def eliminated_b(self) -> bool:
        return "B" in self.eliminated.get(self.current_qid, [])

    @rx.var
    def eliminated_c(self) -> bool:
        return "C" in self.eliminated.get(self.current_qid, [])

    @rx.var
    def eliminated_d(self) -> bool:
        return "D" in self.eliminated.get(self.current_qid, [])

    # ── feedback computed vars ────────────────────────────────
    @rx.var
    def has_current_feedback(self) -> bool:
        return self.current_qid in self.feedback

    @rx.var
    def current_correct_answer(self) -> str:
        return self.feedback.get(self.current_qid, {}).get("correct_answer", "")

    @rx.var
    def current_is_correct(self) -> bool:
        return bool(self.feedback.get(self.current_qid, {}).get("is_correct", False))

    @rx.var
    def correct_a(self) -> bool:
        return self.has_current_feedback and self.current_correct_answer == "A"

    @rx.var
    def correct_b(self) -> bool:
        return self.has_current_feedback and self.current_correct_answer == "B"

    @rx.var
    def correct_c(self) -> bool:
        return self.has_current_feedback and self.current_correct_answer == "C"

    @rx.var
    def correct_d(self) -> bool:
        return self.has_current_feedback and self.current_correct_answer == "D"

    @rx.var
    def wrong_a(self) -> bool:
        return self.has_current_feedback and self.selected_a and not self.current_is_correct

    @rx.var
    def wrong_b(self) -> bool:
        return self.has_current_feedback and self.selected_b and not self.current_is_correct

    @rx.var
    def wrong_c(self) -> bool:
        return self.has_current_feedback and self.selected_c and not self.current_is_correct

    @rx.var
    def wrong_d(self) -> bool:
        return self.has_current_feedback and self.selected_d and not self.current_is_correct

    # ── 設定頁事件 ────────────────────────────────────────────
    async def load_subjects(self):
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BACKEND_URL}/subjects/")
        if resp.status_code == 200:
            self.subjects = resp.json()

    async def load_available_exams(self):
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/questions/exams/list",
                params={"subject_id": self.selected_subject_id},
            )
        if resp.status_code == 200:
            self.available_exams = resp.json()
            if self.available_exams:
                self.selected_year = self.available_exams[0]["year"]
                self.selected_sitting = self.available_exams[0]["sitting"]

    def set_subject(self, value: str):
        self.selected_subject_id = int(value)
        return ExamState.load_available_exams

    def set_mode(self, value: str):
        self.selected_mode = value

    def set_count(self, value: str):
        self.selected_count = int(value)

    def set_year(self, value: str):
        self.selected_year = int(value)

    def set_sitting(self, value: str):
        self.selected_sitting = int(value)

    def toggle_shuffle(self, value: bool):
        self.shuffle_options = value

    def toggle_timed(self, value: bool):
        self.timed = value

    def toggle_instant_review(self, value: bool):
        self.instant_review = value

    def toggle_save_history(self, value: bool):
        self.save_to_history = value

    # ── 開始 / 重做考試 ───────────────────────────────────────
    async def restart_exam(self):
        self.current_index = 0
        self.selected_answers = {}
        self.eliminated = {}
        self.feedback = {}
        self.answered_via_api = {}
        self.time_left = 0
        self.is_timer_running = False
        return ExamState.start_exam

    async def start_exam(self):
        auth = await self.get_state(AuthState)
        t = auth.token
        if not t:
            return rx.redirect("/")

        self.is_loading = True
        self.error_msg = ""

        payload = {
            "subject_id": self.selected_subject_id,
            "mode": self.selected_mode,
            "question_count": self.selected_count,
            "year": self.selected_year if self.selected_mode != "multi_random" else None,
            "sitting": self.selected_sitting if self.selected_mode != "multi_random" else None,
            "shuffle_options": self.shuffle_options,
            "timed": self.timed,
            "instant_review": self.instant_review,
            "save_to_history": self.save_to_history,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/exam/start",
                params={"token": t},
                json=payload,
            )

        self.is_loading = False
        if resp.status_code != 200:
            self.error_msg = f"開始失敗：{resp.json().get('detail', '未知錯誤')}"
            return

        data = resp.json()
        self.session_id = data["session_id"]
        self.questions = data["questions"]
        self.current_index = 0
        self.selected_answers = {}
        self.eliminated = {}
        self.feedback = {}
        self.answered_via_api = {}

        if self.timed:
            self.time_left = len(self.questions) * 90
            self.is_timer_running = True
            return [rx.redirect("/exam"), ExamState.run_timer]
        return rx.redirect("/exam")

    # ── 計時器背景任務 ────────────────────────────────────────
    @rx.event(background=True)
    async def run_timer(self):
        import asyncio
        while True:
            await asyncio.sleep(1)
            expired = False
            async with self:
                if not self.is_timer_running:
                    return
                self.time_left -= 1
                if self.time_left <= 0:
                    self.is_timer_running = False
                    expired = True
            if expired:
                yield ExamState.submit_exam
                return

    # ── 答題介面事件 ──────────────────────────────────────────
    def select_option(self, option: str):
        qid = self.current_qid
        if not qid:
            return
        if self.selected_answers.get(qid) == option:
            new = dict(self.selected_answers)
            new.pop(qid, None)
            self.selected_answers = new
        else:
            self.selected_answers = {**self.selected_answers, qid: option}

    def toggle_eliminate(self, option: str):
        qid = self.current_qid
        if not qid:
            return
        current = list(self.eliminated.get(qid, []))
        if option in current:
            current.remove(option)
        else:
            current.append(option)
        self.eliminated = {**self.eliminated, qid: current}

    def go_next(self):
        if self.current_index < self.total_questions - 1:
            self.current_index += 1

    def go_prev(self):
        if self.current_index > 0:
            self.current_index -= 1

    async def submit_exam(self):
        if not self.session_id or self.is_loading:
            return
        self.is_loading = True
        self.is_timer_running = False
        auth = await self.get_state(AuthState)
        t = auth.token
        async with httpx.AsyncClient() as client:
            for qid, chosen in self.selected_answers.items():
                await client.post(
                    f"{BACKEND_URL}/exam/{self.session_id}/answer",
                    params={"token": t},
                    json={"question_id": qid, "chosen": chosen},
                )
            resp = await client.post(
                f"{BACKEND_URL}/exam/{self.session_id}/submit",
                params={"token": t},
            )
        self.is_loading = False
        if resp.status_code == 400:
            self.session_id = ""
            return rx.redirect("/exam-setup")
        if resp.status_code == 200:
            data = resp.json()
            self.result_score = data.get("score", 0)
            self.result_total = data.get("total", 0)
            self.result_percentage = data.get("percentage", 0.0)
            self.result_details = [
                ResultDetail(
                    order=d.get("order", 0),
                    content=d.get("content", ""),
                    chosen=d.get("chosen") or "",
                    correct_answer=d.get("correct_answer") or "",
                    is_correct=bool(d.get("is_correct", False)),
                    is_unanswered=d.get("chosen") is None,
                )
                for d in data.get("details", [])
            ]
            self.session_id = ""
            return rx.redirect("/result")
