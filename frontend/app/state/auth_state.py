import httpx
import reflex as rx

BACKEND_URL = "http://localhost:8000"


class AuthState(rx.State):
    token: str = rx.LocalStorage("")
    user_name: str = ""
    user_email: str = ""
    user_avatar: str = ""

    def handle_callback(self):
        """OAuth callback：從 URL path param 讀取 token，存入 LocalStorage 後導向主選單。"""
        token = self.router.page.params.get("token", "")
        if not token:
            return rx.redirect("/")
        self.token = token
        return rx.redirect("/home")

    async def load_user(self):
        """主選單頁 on_load：用 token 向後端拿使用者資料。"""
        if not self.token:
            return rx.redirect("/")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/users/me",
                params={"token": self.token},
            )
        if resp.status_code != 200:
            self.token = ""
            return rx.redirect("/")
        data = resp.json()
        self.user_name = data["name"]
        self.user_email = data["email"]
        self.user_avatar = data.get("avatar_url", "")

    def logout(self):
        self.token = ""
        self.user_name = ""
        self.user_email = ""
        self.user_avatar = ""
        return rx.redirect("/")
