import reflex as rx

config = rx.Config(
    app_name="app",
    frontend_port=3000,
    backend_port=8001,  # Reflex 內部 backend，避免與 FastAPI :8000 衝突
)
