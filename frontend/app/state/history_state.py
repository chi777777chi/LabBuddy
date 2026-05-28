from datetime import datetime
import httpx
import reflex as rx
from pydantic import BaseModel
from .auth_state import AuthState, BACKEND_URL, BACKEND_PUBLIC_URL

MODE_LABELS = {
    "single_full": "完整考卷",
    "single_random": "單卷隨機",
    "multi_random": "多卷混合",
}
SITTING_LABELS = {1: "第一次", 2: "第二次"}


class HistoryItem(BaseModel):
    session_id: str = ""
    subject_name: str = ""
    year_label: str = ""      # 114年第二次 / 多年混合
    mode_label: str = ""
    question_count: int = 0
    score: int = 0
    percentage: float = 0.0
    timed: bool = False
    finished_at: str = ""


class HistoryDetail(BaseModel):
    order: int = 0
    question_id: str = ""
    content: str = ""
    chosen: str = ""
    correct_answer: str = ""
    is_correct: bool = False
    is_unanswered: bool = False


class HistoryState(rx.State):
    # ── 清單 ──────────────────────────────────────────────────
    items: list[HistoryItem] = []
    is_loading: bool = False

    # ── 詳情 dialog ───────────────────────────────────────────
    is_detail_open: bool = False
    is_detail_loading: bool = False
    detail_session_id: str = ""
    detail_subject: str = ""
    detail_year_sitting: str = ""
    detail_score: int = 0
    detail_total: int = 0
    detail_items: list[HistoryDetail] = []

    # ── AI 解析 ───────────────────────────────────────────────
    show_explain_dialog: bool = False
    explain_loading: bool = False
    explain_text: str = ""
    explain_question_label: str = ""

    @rx.var
    def has_history(self) -> bool:
        return len(self.items) > 0

    @rx.var
    def detail_score_display(self) -> str:
        return f"{self.detail_score} / {self.detail_total}"

    # ── 載入歷史清單 ──────────────────────────────────────────
    async def load_history(self):
        auth = await self.get_state(AuthState)
        t = auth.token
        if not t:
            return rx.redirect("/")
        self.is_loading = True
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/exam/history",
                params={"token": t},
            )
        self.is_loading = False
        if resp.status_code != 200:
            return
        items = []
        for item in resp.json():
            finished_str = ""
            if item.get("finished_at"):
                try:
                    dt = datetime.fromisoformat(item["finished_at"])
                    finished_str = dt.strftime("%Y/%m/%d %H:%M")
                except Exception:
                    finished_str = item["finished_at"]

            mode = item["mode"]
            year = item.get("year")
            sitting = item.get("sitting")
            if mode == "multi_random":
                year_label = "多年混合"
            elif year and sitting:
                year_label = f"{year}年{SITTING_LABELS.get(sitting, '')}"
            else:
                year_label = ""

            items.append(HistoryItem(
                session_id=item["session_id"],
                subject_name=item["subject_name"],
                year_label=year_label,
                mode_label=MODE_LABELS.get(mode, mode),
                question_count=item["question_count"],
                score=item["score"],
                percentage=item["percentage"],
                timed=item["timed"],
                finished_at=finished_str,
            ))
        self.items = items

    # ── 載入單次詳情 ──────────────────────────────────────────
    async def download_pdf(self):
        auth = await self.get_state(AuthState)
        url = f"{BACKEND_PUBLIC_URL}/exam/{self.detail_session_id}/export-pdf?token={auth.token}"
        return rx.redirect(url, is_external=True)

    async def load_detail(self, session_id: str):
        self.is_detail_open = True
        self.is_detail_loading = True
        self.detail_session_id = session_id
        self.detail_items = []
        auth = await self.get_state(AuthState)
        t = auth.token
        if not t:
            return
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/exam/{session_id}/detail",
                params={"token": t},
            )
        self.is_detail_loading = False
        if resp.status_code != 200:
            return
        data = resp.json()
        self.detail_subject = data["subject_name"]
        self.detail_score = data.get("score", 0)
        self.detail_total = data.get("question_count", 0)
        mode = data.get("mode", "")
        year = data.get("year")
        sitting = data.get("sitting")
        if mode == "multi_random":
            self.detail_year_sitting = "多年混合"
        elif year and sitting:
            self.detail_year_sitting = f"{year}年{SITTING_LABELS.get(sitting, '')}"
        else:
            self.detail_year_sitting = ""
        self.detail_items = [
            HistoryDetail(
                order=d["order"],
                question_id=d.get("question_id", ""),
                content=d.get("content", ""),
                chosen=d.get("chosen") or "",
                correct_answer=d.get("correct_answer") or "",
                is_correct=bool(d.get("is_correct", False)),
                is_unanswered=d.get("chosen") is None,
            )
            for d in data.get("details", [])
        ]

    def set_is_detail_open(self, value: bool):
        self.is_detail_open = value
        if not value:
            self.detail_items = []

    def set_show_explain_dialog(self, value: bool):
        self.show_explain_dialog = value
        if not value:
            self.explain_text = ""

    async def fetch_explain(self, question_id: str, chosen: str, order: int = 0):
        if self.explain_loading or not question_id:
            return
        self.explain_loading = True
        self.explain_text = ""
        self.explain_question_label = f"第 {order} 題"
        self.show_explain_dialog = True
        auth = await self.get_state(AuthState)
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{BACKEND_URL}/ai/explain",
                    params={"token": auth.token},
                    json={"question_id": question_id, "chosen": chosen or None},
                )
            if resp.status_code == 200:
                self.explain_text = resp.json().get("explain", "")
            else:
                self.explain_text = "無法取得解析，請稍後再試。"
        except Exception:
            self.explain_text = "無法取得解析，請稍後再試。"
        finally:
            self.explain_loading = False
