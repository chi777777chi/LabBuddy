import httpx
import reflex as rx
from pydantic import BaseModel
from .auth_state import AuthState, BACKEND_URL


class SubjectStat(BaseModel):
    subject_id: int = 0
    subject_name: str = ""
    wrong_question_count: int = 0
    total_wrong: int = 0
    total_correct: int = 0


class WrongReviewState(rx.State):
    stats: list[SubjectStat] = []
    is_loading: bool = False

    @rx.var
    def has_wrong_questions(self) -> bool:
        return len(self.stats) > 0

    async def load_stats(self):
        auth = await self.get_state(AuthState)
        t = auth.token
        if not t:
            return rx.redirect("/")
        self.is_loading = True
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/exam/wrong-questions",
                params={"token": t},
            )
        self.is_loading = False
        if resp.status_code == 200:
            self.stats = [SubjectStat(**item) for item in resp.json()]
