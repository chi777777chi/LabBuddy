import httpx
import os
import reflex as rx

BACKEND_URL = "http://localhost:8000"
# 使用者瀏覽器可直接訪問的後端 URL（用於 redirect，如 PDF 下載）
# Server 上由 systemd 環境變數注入，本機 fallback 到 localhost:8000
BACKEND_PUBLIC_URL = os.environ.get("BACKEND_PUBLIC_URL", "http://localhost:8000")


class AuthState(rx.State):
    token: str = rx.LocalStorage("")
    user_name: str = ""
    user_email: str = ""
    user_avatar: str = ""
    user_role: str = ""

    async def handle_callback(self):
        """OAuth callback：從 URL query string 讀取 token，存入 LocalStorage 後依角色導向。"""
        token = self.router.page.params.get("jwt", "")
        if not token:
            # fallback: parse manually from raw_path query string
            raw = getattr(self.router.page, "raw_path", "") or ""
            if "jwt=" in raw:
                token = raw.split("jwt=", 1)[1].split("&", 1)[0]
        if not token:
            return rx.redirect("/")
        self.token = token
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}/users/me",
                params={"token": token},
            )
        if resp.status_code == 200:
            role = resp.json().get("role", "student")
            if role == "teacher":
                return rx.redirect("/teacher")
            if role == "admin":
                return rx.redirect("/admin")
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
        self.user_role = data.get("role", "student")

    def logout(self):
        self.token = ""
        self.user_name = ""
        self.user_email = ""
        self.user_avatar = ""
        self.user_role = ""
        return rx.redirect("/")
