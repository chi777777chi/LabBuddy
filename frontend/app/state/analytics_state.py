import httpx
import reflex as rx
from .auth_state import AuthState, BACKEND_URL


class AnalyticsState(rx.State):
    subject_stats: list[dict] = []
    score_trend: list[dict] = []
    weak_questions: list[dict] = []
    ai_analysis: str = ""
    trend_direction: str = "none"
    is_loading: bool = False
    has_loaded: bool = False
    error_msg: str = ""

    @rx.var
    def has_data(self) -> bool:
        return any(s.get("total_answered", 0) > 0 for s in self.subject_stats)

    @rx.var
    def answered_subjects(self) -> list[dict]:
        return [s for s in self.subject_stats if s.get("total_answered", 0) > 0]

    @rx.var
    def weak_subjects(self) -> list[dict]:
        return [s for s in self.subject_stats if s.get("color") == "red" and s.get("total_answered", 0) > 0]

    @rx.var
    def ok_subjects(self) -> list[dict]:
        return [s for s in self.subject_stats if s.get("color") == "orange" and s.get("total_answered", 0) > 0]

    @rx.var
    def strong_subjects(self) -> list[dict]:
        return [s for s in self.subject_stats if s.get("color") == "green" and s.get("total_answered", 0) > 0]

    async def load_analytics(self):
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        self.is_loading = True
        self.has_loaded = False
        self.error_msg = ""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(
                    f"{BACKEND_URL}/analytics/me",
                    params={"token": auth.token},
                )
            if resp.status_code != 200:
                self.error_msg = "載入失敗，請稍後再試。"
            else:
                data = resp.json()
                self.subject_stats = data.get("subject_stats", [])
                self.score_trend = data.get("score_trend", [])
                self.weak_questions = data.get("weak_questions", [])
                self.ai_analysis = data.get("ai_analysis", "")
                self.trend_direction = data.get("trend_direction", "none")
        except Exception:
            self.error_msg = "無法連線至伺服器，請確認後端是否運行。"
        finally:
            self.is_loading = False
            self.has_loaded = True
