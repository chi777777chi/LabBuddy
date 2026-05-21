import httpx
import reflex as rx
from .auth_state import AuthState, BACKEND_URL


class AnalyticsState(rx.State):
    subject_stats: list[dict] = []
    score_trend: list[dict] = []
    weak_questions: list[dict] = []
    ai_analysis: str = ""
    is_loading: bool = False
    error_msg: str = ""

    @rx.var
    def has_data(self) -> bool:
        return any(s.get("total_answered", 0) > 0 for s in self.subject_stats)

    @rx.var
    def answered_subjects(self) -> list[dict]:
        return [s for s in self.subject_stats if s.get("total_answered", 0) > 0]

    async def load_analytics(self):
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        self.is_loading = True
        self.error_msg = ""
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(
                f"{BACKEND_URL}/analytics/me",
                params={"token": auth.token},
            )
        self.is_loading = False
        if resp.status_code != 200:
            self.error_msg = "載入失敗，請稍後再試。"
            return
        data = resp.json()
        self.subject_stats = data.get("subject_stats", [])
        self.score_trend = data.get("score_trend", [])
        self.weak_questions = data.get("weak_questions", [])
        self.ai_analysis = data.get("ai_analysis", "")
