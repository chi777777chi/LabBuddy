import httpx
import reflex as rx
from .auth_state import AuthState, BACKEND_URL


class AnalyticsState(rx.State):
    subject_stats: list[dict] = []
    score_trend: list[dict] = []
    weak_questions: list[dict] = []
    ai_analysis: str = ""
    trend_direction: str = "none"
    time_stats: dict = {}
    is_loading: bool = False
    has_loaded: bool = False
    error_msg: str = ""
    _bg_token: str = ""

    @rx.var
    def has_data(self) -> bool:
        return any(s.get("total_answered", 0) > 0 for s in self.subject_stats)

    # ── 時間效率 computed vars ────────────────────────────────
    @rx.var
    def time_has_data(self) -> bool:
        return bool(self.time_stats.get("has_data", False))

    @rx.var
    def time_avg_seconds(self) -> float:
        return float(self.time_stats.get("avg_time_seconds", 0))

    @rx.var
    def time_speed_ratio(self) -> float:
        return float(self.time_stats.get("speed_ratio", 1.0))

    @rx.var
    def time_slow_count(self) -> int:
        return int(self.time_stats.get("slow_count", 0))

    @rx.var
    def time_fast_count(self) -> int:
        return int(self.time_stats.get("fast_count", 0))

    @rx.var
    def time_total_with_time(self) -> int:
        return int(self.time_stats.get("total_answered_with_time", 0))

    @rx.var
    def time_speed_label(self) -> str:
        ratio = float(self.time_stats.get("speed_ratio", 1.0))
        if ratio > 1.3:
            return "偏慢"
        if ratio < 0.5:
            return "偏快"
        return "適中"

    @rx.var
    def time_speed_color(self) -> str:
        ratio = float(self.time_stats.get("speed_ratio", 1.0))
        if ratio > 1.3:
            return "red"
        if ratio < 0.5:
            return "orange"
        return "green"

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
        """Step 1 (regular handler): reads auth token, sets up loading state, triggers background fetch."""
        if self.is_loading or (self.has_loaded and not self.error_msg):
            return
        auth = await self.get_state(AuthState)
        if not auth.token:
            return
        self._bg_token = auth.token
        self.is_loading = True
        self.has_loaded = False
        self.error_msg = ""
        return AnalyticsState.bg_fetch_analytics

    @rx.event(background=True)
    async def bg_fetch_analytics(self):
        """Step 2 (background task): performs HTTP request without holding the state lock."""
        async with self:
            token = self._bg_token

        error = ""
        result = None
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(
                    f"{BACKEND_URL}/analytics/me",
                    params={"token": token},
                )
            if resp.status_code != 200:
                error = "載入失敗，請稍後再試。"
            else:
                result = resp.json()
        except Exception:
            error = "無法連線至伺服器，請確認後端是否運行。"

        async with self:
            self.is_loading = False
            self.has_loaded = True
            if error:
                self.error_msg = error
            elif result is not None:
                self.subject_stats = result.get("subject_stats", [])
                self.score_trend = result.get("score_trend", [])
                self.weak_questions = result.get("weak_questions", [])
                self.ai_analysis = result.get("ai_analysis", "")
                self.trend_direction = result.get("trend_direction", "none")
                self.time_stats = result.get("time_stats", {})
