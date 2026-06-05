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
    is_embedded_browser: bool = False
    browser_detected: bool = False
    show_suspended_error: bool = False

    def check_login_error(self):
        """登入頁 on_load：檢查 URL 是否帶有 error=suspended 參數。"""
        error = self.router.page.params.get("error", "")
        self.show_suspended_error = error == "suspended"

    def set_embedded_browser(self, val: str):
        self.is_embedded_browser = val == "true"
        self.browser_detected = True

    def detect_browser(self):
        """偵測是否在 LINE / Instagram / WebView 等內建瀏覽器中開啟。"""
        return rx.call_script(
            """
            (function() {
                var ua = navigator.userAgent || '';
                var knownApps = /FBAN|FBAV|Instagram|Line\\/|MicroMessenger|WeChat|GSA/.test(ua);
                var iosWebview = /iPhone|iPad|iPod/.test(ua) && !ua.includes('Version/');
                var androidWebview = /Android/.test(ua) && /wv/.test(ua);
                return (knownApps || iosWebview || androidWebview) ? 'true' : 'false';
            })()
            """,
            callback=AuthState.set_embedded_browser,
        )

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
        if resp.status_code == 403:
            self.token = ""
            return rx.redirect("/?error=suspended")
        if resp.status_code == 200:
            role = resp.json().get("role", "student")
            if role == "teacher":
                return rx.redirect("/teacher")
            if role == "admin":
                return rx.redirect("/admin")
        return rx.redirect("/home")

    @rx.event(background=True)
    async def load_user(self):
        """主選單頁 on_load：用 token 向後端拿使用者資料。"""
        async with self:
            token = self.token
        if not token:
            yield rx.redirect("/")
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{BACKEND_URL}/users/me",
                    params={"token": token},
                )
        except Exception:
            return
        if resp.status_code in (401, 403):
            async with self:
                self.token = ""
            yield rx.redirect("/?error=suspended" if resp.status_code == 403 else "/")
            return
        if resp.status_code != 200:
            return
        data = resp.json()
        async with self:
            self.user_name = data["name"]
            self.user_email = data["email"]
            self.user_avatar = data.get("avatar_url", "")
            self.user_role = data.get("role", "student")

    async def init_analytics(self):
        from app.state.analytics_state import AnalyticsState
        if not self.token:
            return
        return AnalyticsState.start_load(self.token)

    def logout(self):
        self.token = ""
        self.user_name = ""
        self.user_email = ""
        self.user_avatar = ""
        self.user_role = ""
        return rx.redirect("/")
