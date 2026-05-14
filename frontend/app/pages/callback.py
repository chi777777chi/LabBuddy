import reflex as rx
from ..state.auth_state import AuthState


@rx.page(route="/callback/[token]", on_load=AuthState.handle_callback)
def callback_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("登入中，請稍候…", color_scheme="gray"),
            align="center",
            spacing="4",
        ),
        height="100vh",
    )
