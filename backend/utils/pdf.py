import io
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

# ── CJK 字型偵測 ──────────────────────────────────────────────
_FONT_NAME = "Helvetica"
_FONT_READY = False


def _get_font() -> str:
    global _FONT_NAME, _FONT_READY
    if _FONT_READY:
        return _FONT_NAME

    candidates = [
        "C:/Windows/Fonts/msjh.ttc",          # Windows：微軟正黑體
        "C:/Windows/Fonts/mingliu.ttc",        # Windows：細明體
        "C:/Windows/Fonts/simsun.ttc",         # Windows：新細明體
        "/System/Library/Fonts/PingFang.ttc",  # macOS
        "/usr/share/fonts/truetype/noto/NotoSansCJKtc-Regular.otf",  # Linux
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("CJKFont", path))
                _FONT_NAME = "CJKFont"
                break
            except Exception:
                continue

    _FONT_READY = True
    return _FONT_NAME


# ── 主要產生函式 ──────────────────────────────────────────────
def generate_exam_pdf(
    subject_name: str,
    year_sitting: str,
    mode_label: str,
    finished_at: str,
    score: int,
    total: int,
    percentage: float,
    details: list,
) -> bytes:
    font = _get_font()

    def style(size: int, bold: bool = False, color=colors.black, space_after: int = 4) -> ParagraphStyle:
        return ParagraphStyle(
            f"st_{size}_{bold}_{id(color)}",
            fontName=font,
            fontSize=size,
            leading=round(size * 1.55),
            textColor=color,
            spaceAfter=space_after,
        )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
        topMargin=2 * cm,    bottomMargin=2 * cm,
    )

    blue  = colors.HexColor("#2563EB")
    green = colors.HexColor("#16A34A")
    red   = colors.HexColor("#DC2626")
    gray  = colors.HexColor("#6B7280")

    content = []

    # ── 頁首：標題 ──
    # 格式："{year_sitting} {科目} 測驗紀錄"（如 114年第二次 臨床生理學與病理學 測驗紀錄）
    title_text = f"{year_sitting + ' ' if year_sitting else ''}{subject_name}　測驗紀錄"
    content.append(Paragraph(title_text, style(14, color=blue, space_after=6)))

    # 日期 + 答對率
    date_str = finished_at.replace("/", "-") if finished_at else ""
    content.append(Paragraph(
        f"日期：{date_str}　　答對率：{score} / {total}（{percentage}%）",
        style(10, color=gray, space_after=2),
    ))
    content.append(HRFlowable(width="100%", thickness=1, color=blue, spaceAfter=12))

    # ── 各題區塊 ──
    for d in details:
        order = d["order"]
        is_unanswered = (d["chosen"] == "未作答")

        if is_unanswered:
            mark = "[ — ] 未作答"
            mark_color = gray
        elif d["is_correct"]:
            mark = "[V] 正確"
            mark_color = green
        else:
            mark = "[X] 錯誤"
            mark_color = red

        # 第N題　[V] 正確
        content.append(Paragraph(
            f"第 {order} 題　　{mark}",
            style(11, color=mark_color, space_after=3),
        ))

        # 題目：...（完整）
        content.append(Paragraph(
            f"題目：{d['content']}",
            style(9, space_after=4),
        ))

        # 選項 A / B / C / D
        options = d.get("options", {})
        chosen = d["chosen"]
        correct = d["correct_answer"]
        for letter in ("A", "B", "C", "D"):
            text = options.get(letter, "")
            if not text:
                continue
            is_chosen  = (letter == chosen)
            is_correct_opt = (letter == correct)

            if is_chosen and d["is_correct"]:
                opt_color = green
            elif is_chosen and not d["is_correct"]:
                opt_color = red
            elif is_correct_opt and not d["is_correct"]:
                opt_color = green
            else:
                opt_color = gray

            content.append(Paragraph(
                f"　{letter}.　{text}",
                style(9, color=opt_color, space_after=2),
            ))

        # 你的答案：X　正確答案：Y（摘要行）
        content.append(Spacer(1, 0.15 * cm))
        chosen_display = chosen if not is_unanswered else "（未作答）"
        content.append(Paragraph(
            f"你的答案：{chosen_display}　　正確答案：{correct}",
            style(9, color=gray, space_after=8),
        ))

        content.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#E5E7EB"), spaceAfter=6))

    doc.build(content)
    return buffer.getvalue()
