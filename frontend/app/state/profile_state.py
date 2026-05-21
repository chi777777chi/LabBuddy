import httpx
import reflex as rx
from .auth_state import AuthState, BACKEND_URL


class ProfileState(rx.State):
    joined_date: str = ""
    total_sessions: int = 0
    total_answered: int = 0
    overall_accuracy: float | None = None
    favorite_subject: str = ""
    is_loading: bool = False

    async def load_stats(self):
        auth = await self.get_state(AuthState)
        if not auth.token:
            return rx.redirect("/")
        self.is_loading = True
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/users/me/stats",
                params={"token": auth.token},
            )
        self.is_loading = False
        if resp.status_code == 200:
            data = resp.json()
            self.joined_date = data.get("joined_date", "")
            self.total_sessions = data.get("total_sessions", 0)
            self.total_answered = data.get("total_answered", 0)
            self.overall_accuracy = data.get("overall_accuracy")
            self.favorite_subject = data.get("favorite_subject", "")
