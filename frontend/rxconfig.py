import os
import reflex as rx

config = rx.Config(
    app_name="app",
    frontend_port=3000,
    backend_port=3000,
    api_url=os.environ.get("REFLEX_API_URL", "http://localhost:3000"),
)
