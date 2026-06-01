import reflex as rx
from .pages import login, callback, home, exam_setup, exam, result, history, wrong_review, analytics, profile, admin, admin_users, admin_questions, teacher, teacher_class, teacher_student, teacher_stats, my_class  # noqa: F401 — 匯入即註冊頁面路由

_WEBVIEW_CSS = (
    "body.is-webview #webview-warning{display:flex!important}"
    "body.is-webview #login-btn{display:none!important}"
)

_WEBVIEW_SCRIPT = """
(function(){
    var ua=navigator.userAgent||'';
    var webview=
        /FBAN|FBAV|Instagram|Line\\/|MicroMessenger|WeChat|GSA/.test(ua)||
        (/iPhone|iPad|iPod/.test(ua)&&!ua.includes('Version/'))||
        (/Android/.test(ua)&&/wv/.test(ua));
    if(!webview)return;
    function mark(){
        if(document.body){document.body.classList.add('is-webview');}
        else{setTimeout(mark,10);}
    }
    if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',mark);}
    else{mark();}
})();
"""

app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="blue",
        radius="medium",
    ),
    stylesheets=["custom.css"],
    head_components=[
        rx.html(f"<style>{_WEBVIEW_CSS}</style>"),
        rx.script(_WEBVIEW_SCRIPT),
    ],
)
