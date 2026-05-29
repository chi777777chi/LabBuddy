import httpx
import reflex as rx
import time as _time
from pydantic import BaseModel
from .auth_state import AuthState, BACKEND_URL, BACKEND_PUBLIC_URL


class ResultDetail(BaseModel):
    order: int = 0
    question_id: str = ""
    content: str = ""
    chosen: str = ""
    correct_answer: str = ""
    is_correct: bool = False
    is_unanswered: bool = False
    time_spent_seconds: int = 0


class ExamState(rx.State):
    # ── 設定頁 ────────────────────────────────────────────────
    subjects: list[dict] = []
    selected_subject_id: int = 1
    selected_mode: str = "single_full"
    selected_count: int = 10
    selected_year: int = 114
    selected_sitting: int = 2
    selected_difficulty: str = "all"
    shuffle_options: bool = False
    timed: bool = False
    instant_review: bool = True
    save_to_history: bool = True
    available_exams: list[dict] = []
    is_loading_exams: bool = False

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

    # ── 計時器（碼表，計總時間） ──────────────────────────────
    elapsed_seconds: int = 0
    show_time_breakdown: bool = True   # 作答後是否顯示各題用時分析
    is_timer_running: bool = False

    # ── 放棄確認 dialog ───────────────────────────────────────
    show_quit_dialog: bool = False

    # ── 提早交卷確認 dialog ───────────────────────────────────
    show_early_submit_dialog: bool = False

    # ── 即時對答回饋等待 ──────────────────────────────────────
    is_showing_feedback: bool = False  # 顯示回饋中（2 秒鎖定）
    pending_submit: bool = False       # 2 秒後要交卷（而非下一題）

    # ── AI Hint ───────────────────────────────────────────────
    use_ai_hint: bool = False
    show_ai_hint_dialog: bool = False
    ai_hint_text: str = ""
    ai_hint_loading: bool = False
    hint_levels: dict[str, int] = {}  # {question_id: 已看層數}

    # ── AI 解析 ───────────────────────────────────────────────
    show_explain_dialog: bool = False
    explain_loading: bool = False
    explain_text: str = ""
    explain_question_label: str = ""
    # private vars for background task handoff (not sent to frontend)
    _bg_explain_token: str = ""
    _bg_explain_qid: str = ""
    _bg_explain_chosen: str = ""
    _bg_hint_token: str = ""
    _bg_hint_qid: str = ""
    _bg_hint_next_level: int = 0

    # ── 每題計時 ─────────────────────────────────────────────
    q_start_time: dict[str, float] = {}   # {qid: timestamp when user arrived}
    q_time_spent: dict[str, int] = {}     # {qid: accumulated seconds}

    # ── 成績 ─────────────────────────────────────────────────
    result_score: int = 0
    result_total: int = 0
    result_percentage: float = 0.0
    result_details: list[ResultDetail] = []
    result_session_id: str = ""       # 交卷後保留 session_id 供 PDF 匯出
    result_elapsed_seconds: int = 0   # 本場總作答秒數
    result_show_time_breakdown: bool = False  # 是否顯示各題用時分析

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
    def unanswered_count(self) -> int:
        return len(self.questions) - len(self.selected_answers)

    @rx.var
    def all_answered(self) -> bool:
        return len(self.selected_answers) == len(self.questions) and len(self.questions) > 0

    @rx.var
    def is_current_answered(self) -> bool:
        """即時對答模式下，當前題目是否已送出（鎖定）"""
        return self.current_qid in self.answered_via_api

    @rx.var
    def is_wrong_review(self) -> bool:
        if not self.questions:
            return False
        return "wrong_count" in self.questions[0]

    @rx.var
    def current_wrong_count(self) -> int:
        if not self.questions or self.current_index >= len(self.questions):
            return 0
        return self.questions[self.current_index].get("wrong_count", 0)

    @rx.var
    def current_correct_count(self) -> int:
        if not self.questions or self.current_index >= len(self.questions):
            return 0
        return self.questions[self.current_index].get("correct_count", 0)

    @rx.var
    def current_qid(self) -> str:
        if not self.questions or self.current_index >= len(self.questions):
            return ""
        return self.questions[self.current_index].get("question_id", "")

    @rx.var
    def time_display(self) -> str:
        mins = self.elapsed_seconds // 60
        secs = self.elapsed_seconds % 60
        return f"{mins:02d}:{secs:02d}"

    @rx.var
    def result_time_display(self) -> str:
        mins = self.result_elapsed_seconds // 60
        secs = self.result_elapsed_seconds % 60
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
    def current_is_bonus(self) -> bool:
        if not self.questions or self.current_index >= len(self.questions):
            return False
        return bool(self.questions[self.current_index].get("is_bonus", False))

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
    def current_chosen(self) -> str:
        return self.selected_answers.get(self.current_qid, "")

    @rx.var
    def current_hint_level(self) -> int:
        return self.hint_levels.get(self.current_qid, 0)

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

    # ── 每題計時 helpers ──────────────────────────────────────
    def _record_time_for(self, qid: str):
        """累計 qid 的停留時間，並清除其起始時戳。"""
        if not qid:
            return
        start = self.q_start_time.get(qid, 0.0)
        if start > 0.0:
            elapsed = max(0, int(_time.time() - start))
            prev = self.q_time_spent.get(qid, 0)
            self.q_time_spent = {**self.q_time_spent, qid: prev + elapsed}
        new_starts = dict(self.q_start_time)
        new_starts.pop(qid, None)
        self.q_start_time = new_starts

    def _begin_timing(self, qid: str):
        """開始記錄 qid 的停留時間。"""
        if not qid:
            return
        self.q_start_time = {**self.q_start_time, qid: _time.time()}

    # ── 設定頁事件 ────────────────────────────────────────────
    async def load_subjects(self):
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BACKEND_URL}/subjects/")
        if resp.status_code == 200:
            self.subjects = resp.json()

    async def load_available_exams(self):
        self.is_loading_exams = True
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/questions/exams/list",
                params={"subject_id": self.selected_subject_id},
            )
        self.is_loading_exams = False
        if resp.status_code == 200:
            sitting_label = {1: "第一次", 2: "第二次"}
            self.available_exams = [
                {
                    **e,
                    "label": f"{e['year']}年{sitting_label.get(e['sitting'], '')}",
                    "combo": f"{e['year']}-{e['sitting']}",
                }
                for e in resp.json()
            ]
            if self.available_exams:
                # 只有當前選擇不在新列表中時才重置（切換科目時）
                current_valid = any(
                    e["year"] == self.selected_year and e["sitting"] == self.selected_sitting
                    for e in self.available_exams
                )
                if not current_valid:
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

    def set_difficulty(self, value: str):
        self.selected_difficulty = value

    def set_exam(self, value: str):
        """設定考古題年份＋梯次（格式：'114-1'）"""
        parts = value.split("-")
        if len(parts) == 2:
            self.selected_year = int(parts[0])
            self.selected_sitting = int(parts[1])

    @rx.var
    def selected_exam_value(self) -> str:
        return f"{self.selected_year}-{self.selected_sitting}"

    @rx.var
    def selected_exam_label(self) -> str:
        sitting_label = {1: "第一次", 2: "第二次"}
        return f"{self.selected_year}年{sitting_label.get(self.selected_sitting, '')}"

    def toggle_shuffle(self, value: bool):
        self.shuffle_options = value

    def toggle_timed(self, value: bool):
        self.timed = value

    def toggle_time_breakdown(self, value: bool):
        self.show_time_breakdown = value

    def toggle_instant_review(self, value: bool):
        self.instant_review = value

    def toggle_save_history(self, value: bool):
        self.save_to_history = value

    # ── 開始 / 重做考試 ───────────────────────────────────────
    def open_quit_dialog(self):
        self.show_quit_dialog = True

    def set_show_quit_dialog(self, value: bool):
        self.show_quit_dialog = value

    async def download_result_pdf(self):
        auth = await self.get_state(AuthState)
        url = f"{BACKEND_PUBLIC_URL}/exam/{self.result_session_id}/export-pdf?token={auth.token}"
        return rx.redirect(url, is_external=True)

    def open_early_submit_dialog(self):
        self.show_early_submit_dialog = True

    def set_show_early_submit_dialog(self, value: bool):
        self.show_early_submit_dialog = value

    def confirm_quit(self):
        """放棄此次測驗，不交卷，直接清除 session 回主選單。"""
        self.session_id = ""
        self.questions = []
        self.is_timer_running = False
        self.elapsed_seconds = 0
        self.show_quit_dialog = False
        self.q_start_time = {}
        self.q_time_spent = {}
        return rx.redirect("/home")

    async def start_wrong_review(self, subject_id: int):
        self.selected_subject_id = subject_id
        self.selected_mode = "wrong_review"
        self.selected_count = 999  # 後端會 cap 到實際錯題數
        self.current_index = 0
        self.selected_answers = {}
        self.eliminated = {}
        self.feedback = {}
        self.answered_via_api = {}
        self.elapsed_seconds = 0
        self.is_timer_running = False
        return ExamState.start_exam

    async def restart_exam(self):
        self.current_index = 0
        self.selected_answers = {}
        self.eliminated = {}
        self.feedback = {}
        self.answered_via_api = {}
        self.hint_levels = {}
        self.elapsed_seconds = 0
        self.is_timer_running = False
        self.q_start_time = {}
        self.q_time_spent = {}
        return ExamState.start_exam

    async def start_exam(self):
        auth = await self.get_state(AuthState)
        t = auth.token
        if not t:
            return rx.redirect("/")

        self.is_loading = True
        self.error_msg = ""

        no_year_modes = ("multi_random", "adaptive")
        payload = {
            "subject_id": self.selected_subject_id,
            "mode": self.selected_mode,
            "question_count": self.selected_count,
            "year": self.selected_year if self.selected_mode not in no_year_modes else None,
            "sitting": self.selected_sitting if self.selected_mode not in no_year_modes else None,
            "difficulty": self.selected_difficulty if self.selected_difficulty != "all" else None,
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
        self.hint_levels = {}
        self.q_start_time = {}
        self.q_time_spent = {}
        if self.questions:
            first_qid = self.questions[0].get("question_id", "")
            if first_qid:
                self.q_start_time = {first_qid: _time.time()}

        if self.timed:
            self.elapsed_seconds = 0
            self.is_timer_running = True
            return [rx.redirect("/exam"), ExamState.run_timer]
        return rx.redirect("/exam")

    # ── 計時器背景任務（碼表，計總時間） ─────────────────────
    @rx.event(background=True)
    async def run_timer(self):
        import asyncio
        while True:
            await asyncio.sleep(1)
            async with self:
                if not self.is_timer_running:
                    return
                self.elapsed_seconds += 1

    # ── 答題介面事件 ──────────────────────────────────────────
    def select_option(self, option: str):
        qid = self.current_qid
        if not qid or qid in self.answered_via_api:  # 已送出，鎖定
            return
        if self.selected_answers.get(qid) == option:
            new = dict(self.selected_answers)
            new.pop(qid, None)
            self.selected_answers = new
        else:
            self.selected_answers = {**self.selected_answers, qid: option}

    def toggle_eliminate(self, option: str):
        qid = self.current_qid
        if not qid or qid in self.answered_via_api:  # 已送出，鎖定
            return
        current = list(self.eliminated.get(qid, []))
        if option in current:
            current.remove(option)
        else:
            current.append(option)
        self.eliminated = {**self.eliminated, qid: current}

    def go_next(self):
        if self.questions and self.current_index < len(self.questions):
            self._record_time_for(self.questions[self.current_index].get("question_id", ""))
        if self.current_index < self.total_questions - 1:
            self.current_index += 1
            if self.questions and self.current_index < len(self.questions):
                self._begin_timing(self.questions[self.current_index].get("question_id", ""))

    def go_prev(self):
        if self.questions and self.current_index < len(self.questions):
            self._record_time_for(self.questions[self.current_index].get("question_id", ""))
        if self.current_index > 0:
            self.current_index -= 1
            if self.questions and self.current_index < len(self.questions):
                self._begin_timing(self.questions[self.current_index].get("question_id", ""))

    async def handle_next(self):
        """下一題 / 交卷按鈕：即時對答模式先送 API 顯示回饋 1 秒，再前進。"""
        if self.is_showing_feedback:
            return
        qid = self.current_qid
        chosen = self.selected_answers.get(qid)
        is_last = self.current_index >= len(self.questions) - 1

        # 已送出過（返回後再按下一題）→ 直接前進，不重複顯示回饋
        if qid in self.answered_via_api:
            if is_last:
                return ExamState.submit_exam
            self._record_time_for(qid)
            self.current_index += 1
            if self.questions and self.current_index < len(self.questions):
                self._begin_timing(self.questions[self.current_index].get("question_id", ""))
            return

        self._record_time_for(qid)
        time_spent = self.q_time_spent.get(qid, 0) or None

        if self.instant_review and chosen:
            auth = await self.get_state(AuthState)
            t = auth.token
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{BACKEND_URL}/exam/{self.session_id}/answer",
                    params={"token": t},
                    json={"question_id": qid, "chosen": chosen, "time_spent_seconds": time_spent},
                )
            if resp.status_code == 200:
                data = resp.json()
                self.feedback = {
                    **self.feedback,
                    qid: {
                        "is_correct": data.get("is_correct", False),
                        "correct_answer": data.get("correct_answer", ""),
                    },
                }
                self.answered_via_api = {**self.answered_via_api, qid: True}
            self.is_showing_feedback = True
            self.pending_submit = is_last
            return ExamState.feedback_delay

        if is_last:
            return ExamState.submit_exam
        self.current_index += 1
        if self.questions and self.current_index < len(self.questions):
            self._begin_timing(self.questions[self.current_index].get("question_id", ""))

    @rx.event(background=True)
    async def feedback_delay(self):
        import asyncio
        await asyncio.sleep(1)
        async with self:
            self.is_showing_feedback = False
            self.pending_submit = False

    async def fetch_explain_current(self):
        """Step 1: reads state + auth token, then triggers background AI call."""
        qid = self.current_qid
        chosen = self.selected_answers.get(qid, "")
        order = self.current_index + 1
        if self.explain_loading or not qid:
            return
        auth = await self.get_state(AuthState)
        self._bg_explain_token = auth.token
        self._bg_explain_qid = qid
        self._bg_explain_chosen = chosen
        self.explain_loading = True
        self.explain_text = ""
        self.explain_question_label = f"第 {order} 題"
        self.show_explain_dialog = True
        return ExamState.bg_fetch_explain

    @rx.event(background=True)
    async def bg_fetch_explain(self):
        """Step 2: HTTP request outside lock."""
        async with self:
            token = self._bg_explain_token
            qid = self._bg_explain_qid
            chosen = self._bg_explain_chosen

        explain_text = "無法取得解析，請稍後再試。"
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{BACKEND_URL}/ai/explain",
                    params={"token": token},
                    json={"question_id": qid, "chosen": chosen or None},
                )
            if resp.status_code == 200:
                explain_text = resp.json().get("explain", "")
        except Exception:
            pass

        async with self:
            self.explain_text = explain_text
            self.explain_loading = False

    def toggle_ai_hint(self, value: bool):
        self.use_ai_hint = value

    def close_ai_hint_dialog(self):
        self.show_ai_hint_dialog = False
        self.ai_hint_text = ""

    def set_show_explain_dialog(self, value: bool):
        self.show_explain_dialog = value
        if not value:
            self.explain_text = ""

    async def fetch_explain(self, question_id: str, chosen: str, order: int = 0):
        """Step 1: reads auth token, sets up state, triggers background AI call."""
        if self.explain_loading or not question_id:
            return
        auth = await self.get_state(AuthState)
        self._bg_explain_token = auth.token
        self._bg_explain_qid = question_id
        self._bg_explain_chosen = chosen
        self.explain_loading = True
        self.explain_text = ""
        self.explain_question_label = f"第 {order} 題"
        self.show_explain_dialog = True
        return ExamState.bg_fetch_explain

    async def fetch_ai_hint(self):
        """Step 1: reads state + auth token, triggers background hint call."""
        qid = self.current_qid
        current_level = self.hint_levels.get(qid, 0)
        if self.ai_hint_loading or not qid or current_level >= 3:
            return
        auth = await self.get_state(AuthState)
        self._bg_hint_token = auth.token
        self._bg_hint_qid = qid
        self._bg_hint_next_level = current_level + 1
        self.ai_hint_loading = True
        self.ai_hint_text = ""
        self.show_ai_hint_dialog = True
        return ExamState.bg_fetch_ai_hint

    @rx.event(background=True)
    async def bg_fetch_ai_hint(self):
        """Step 2: HTTP request outside lock."""
        async with self:
            token = self._bg_hint_token
            qid = self._bg_hint_qid
            next_level = self._bg_hint_next_level

        hint_text = "無法取得提示，請稍後再試。"
        new_level = None
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{BACKEND_URL}/ai/hint",
                    params={"token": token},
                    json={"question_id": qid, "level": next_level},
                )
            if resp.status_code == 200:
                hint_text = resp.json().get("hint", "")
                new_level = next_level
        except Exception:
            pass

        async with self:
            self.ai_hint_loading = False
            self.ai_hint_text = hint_text
            if new_level is not None:
                self.hint_levels = {**self.hint_levels, qid: new_level}

    async def submit_exam(self):
        if not self.session_id or self.is_loading:
            return
        self.show_early_submit_dialog = False
        self.is_loading = True
        self.is_timer_running = False
        # 記錄當前題目的停留時間（計時器到期或提早交卷時）
        if self.questions and self.current_index < len(self.questions):
            self._record_time_for(self.questions[self.current_index].get("question_id", ""))
        auth = await self.get_state(AuthState)
        t = auth.token
        async with httpx.AsyncClient() as client:
            for qid, chosen in self.selected_answers.items():
                if qid in self.answered_via_api:  # 即時對答已送過，跳過
                    continue
                time_spent = self.q_time_spent.get(qid, 0) or None
                await client.post(
                    f"{BACKEND_URL}/exam/{self.session_id}/answer",
                    params={"token": t},
                    json={"question_id": qid, "chosen": chosen, "time_spent_seconds": time_spent},
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
            self.result_elapsed_seconds = self.elapsed_seconds
            self.result_show_time_breakdown = self.timed and self.show_time_breakdown
            # 建立 order（1-based）→ time_spent 對照表
            order_to_time: dict[int, int] = {}
            for i, q in enumerate(self.questions):
                qid = q.get("question_id", "")
                order_to_time[i + 1] = self.q_time_spent.get(qid, 0)
            self.result_details = [
                ResultDetail(
                    order=d.get("order", 0),
                    question_id=d.get("question_id", ""),
                    content=d.get("content", ""),
                    chosen=d.get("chosen") or "",
                    correct_answer=d.get("correct_answer") or "",
                    is_correct=bool(d.get("is_correct", False)),
                    is_unanswered=d.get("chosen") is None,
                    time_spent_seconds=order_to_time.get(d.get("order", 0), 0),
                )
                for d in data.get("details", [])
            ]
            self.result_session_id = self.session_id
            self.session_id = ""
            self.elapsed_seconds = 0
            self.is_timer_running = False
            return rx.redirect("/result")
