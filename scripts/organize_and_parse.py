# -*- coding: utf-8 -*-
"""
1. 搬移並重命名所有 PDF 到正確科目資料夾
2. 從答案 PDF 提取標準答案
3. 從題目 PDF 解析題目並產生 JSON
"""
import re, json, shutil, fitz
from pathlib import Path

ROOT = Path(__file__).parent.parent
Q_ROOT = ROOT / "Question"

# ── 1. 搬移計畫 ────────────────────────────────────────────────
MOVES = {
    "824338955.pdf":   ("hematology",           "114-2-hematology.pdf"),
    "870788684.pdf":   ("molecular_lab",         "114-2-molecular_lab.pdf"),
    "557486786.pdf":   ("immunology_virology",   "114-2-immunology_virology.pdf"),
    "114-2-微生物.pdf": ("microbiology",          "114-2-microbiology.pdf"),
    "114-2-生物化學.pdf":("biochemistry",          "114-2-biochemistry.pdf"),
    "521696820.pdf":   ("hematology",            "114-2-hematology-answers.pdf"),
    "204697919.pdf":   ("molecular_lab",         "114-2-molecular_lab-answers.pdf"),
    "269349255.pdf":   ("immunology_virology",   "114-2-immunology_virology-answers.pdf"),
    "567791395.pdf":   ("biochemistry",          "114-2-biochemistry-answers.pdf"),
    "950894142.pdf":   ("microbiology",          "114-2-microbiology-answers.pdf"),
}

SUBJECT_INFO = {
    "hematology":          {"year": 114, "sitting": 2, "name": "臨床血液學與血庫學"},
    "molecular_lab":       {"year": 114, "sitting": 2, "name": "醫學分子檢驗學與臨床鏡檢學"},
    "immunology_virology": {"year": 114, "sitting": 2, "name": "臨床血清免疫學與臨床病毒學"},
    "microbiology":        {"year": 114, "sitting": 2, "name": "微生物學與臨床微生物學"},
    "biochemistry":        {"year": 114, "sitting": 2, "name": "生物化學與臨床生化學"},
}

EXAM_CODES = {
    "hematology": "2308", "molecular_lab": "3308",
    "microbiology": "4308", "biochemistry": "5308", "immunology_virology": "6308",
}


def move_files():
    for old, (folder, new_name) in MOVES.items():
        src = Q_ROOT / old
        dst = Q_ROOT / folder / new_name
        if src.exists():
            shutil.move(str(src), str(dst))
            print(f"  moved: {old} -> {folder}/{new_name}")
        else:
            print(f"  skip (not found): {old}")


# ── 2. 解析答案 PDF ────────────────────────────────────────────
CHAR_MAP = {"Ａ": "A", "Ｂ": "B", "Ｃ": "C", "Ｄ": "D",
            "A": "A", "B": "B", "C": "C", "D": "D"}

def extract_answers(pdf_path: Path) -> dict[int, str]:
    doc = fitz.open(str(pdf_path))
    text = "".join(page.get_text() for page in doc)
    doc.close()

    answers = {}
    # 找「答案 X X X X ...」的行（全形或半形字母）
    pattern = re.compile(r'答案\s*((?:[ＡＢＣＤABCD]\s*){20})')
    rows = pattern.findall(text)
    for i, row in enumerate(rows):
        chars = [CHAR_MAP[c] for c in row.replace(" ", "").replace("\n", "") if c in CHAR_MAP]
        for j, ans in enumerate(chars):
            q_num = i * 20 + j + 1
            answers[q_num] = ans
    return answers


# ── 3. 解析題目 PDF ────────────────────────────────────────────
def extract_text(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    text = "".join(page.get_text() for page in doc)
    doc.close()
    return text


def parse_questions(text: str, answers: dict) -> list[dict]:
    # 切分每題：以「數字.」開頭
    blocks = re.split(r'\n(?=\d{1,2}\.)', text)
    questions = []

    for block in blocks:
        block = block.strip()
        m = re.match(r'^(\d{1,2})\.(.*)', block, re.DOTALL)
        if not m:
            continue
        num = int(m.group(1))
        if num < 1 or num > 80:
            continue

        body = m.group(2).strip()

        # 拆選項：A. B. C. D.（支援全形 A. 或半形 A.）
        opt_pattern = re.compile(r'\n\s*[Ａ-Ｄ A-D]\.')
        parts = opt_pattern.split(body)
        if len(parts) < 5:
            # 備用：找 A～D 行
            opt_pattern2 = re.compile(r'(?:^|\n)\s*([A-D])\.')
            opts_found = opt_pattern2.findall(body)
            if len(opts_found) < 4:
                questions.append({
                    "number": num, "content": body,
                    "options": {"A": "", "B": "", "C": "", "D": ""},
                    "answer": answers.get(num), "has_image": False,
                    "parse_error": True,
                })
                continue
            opt_parts = opt_pattern2.split(body)
            content = opt_parts[0].strip()
            opts = {opt_parts[i]: opt_parts[i+1].strip() for i in range(1, len(opt_parts)-1, 2)}
        else:
            content = parts[0].strip()
            labels = ["A", "B", "C", "D"]
            opts = {labels[i]: parts[i+1].strip() if i+1 < len(parts) else "" for i in range(4)}

        questions.append({
            "number": num,
            "content": content,
            "has_image": False,
            "options": {
                "A": opts.get("A", "").strip(),
                "B": opts.get("B", "").strip(),
                "C": opts.get("C", "").strip(),
                "D": opts.get("D", "").strip(),
            },
            "answer": answers.get(num),
        })

    questions.sort(key=lambda q: q["number"])
    return questions


# ── 4. 主流程 ─────────────────────────────────────────────────
def main():
    print("=== Step 1: Moving files ===")
    move_files()

    print("\n=== Step 2: Parsing each subject ===")
    for subject_en, info in SUBJECT_INFO.items():
        folder = Q_ROOT / subject_en
        q_pdf  = folder / f"114-2-{subject_en}.pdf"
        a_pdf  = folder / f"114-2-{subject_en}-answers.pdf"
        out    = folder / f"114-2-{subject_en}.json"

        if not q_pdf.exists():
            print(f"  [skip] {subject_en}: question PDF not found")
            continue
        if not a_pdf.exists():
            print(f"  [skip] {subject_en}: answer PDF not found")
            continue

        print(f"\n  [{subject_en}]")
        answers = extract_answers(a_pdf)
        print(f"    answers extracted: {len(answers)}")

        text = extract_text(q_pdf)
        questions = parse_questions(text, answers)
        print(f"    questions parsed:  {len(questions)}")

        errors = [q["number"] for q in questions if q.get("parse_error")]
        if errors:
            print(f"    parse_error on Q: {errors}")

        data = {
            "exam_info": {
                "year": info["year"],
                "sitting": info["sitting"],
                "subject": info["name"],
                "exam_code": EXAM_CODES[subject_en],
                "exam_type": "專技高考醫事檢驗師",
                "duration_minutes": 60,
                "total_questions": 80,
            },
            "questions": questions,
        }
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"    saved: {out.name}")

    print("\nDone.")


if __name__ == "__main__":
    main()
