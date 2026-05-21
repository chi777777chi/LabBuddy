"""
convert_questions_auto.py

Convert question PDFs in subject folders to JSON.

Handles two PDF formats:
  - Old  (year <= 110): answers embedded as （X）N prefix  (補習班解析書)
  - New  (year >= 111): answers on last page in table form (考選部官方試題)

Usage:
    python scripts/convert_questions_auto.py --subject biochemistry
    python scripts/convert_questions_auto.py --subject biochemistry --force
    python scripts/convert_questions_auto.py              # all subjects
"""

import argparse
import json
import os
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pdfplumber

FULLWIDTH = str.maketrans("ＡＢＣＤ", "ABCD")

CODE_TO_FOLDER = {
    "1308": "clinical_physiology",
    "2308": "hematology",
    "3308": "molecular_lab",
    "4308": "microbiology",
    "5308": "biochemistry",
    "6308": "immunology_virology",
}
CODE_TO_SUBJECT_TW = {
    "1308": "臨床生理學與病理學",
    "2308": "臨床血液學與血庫學",
    "3308": "醫學分子檢驗學與臨床鏡檢學",
    "4308": "微生物學與臨床微生物學",
    "5308": "生物化學與臨床生化學",
    "6308": "臨床血清免疫學與臨床病毒學",
}
FOLDER_TO_CODE = {v: k for k, v in CODE_TO_FOLDER.items()}

QUESTION_DIR = os.path.join(os.path.dirname(__file__), "..", "Question")


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def _full_text(path):
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _last_page_text(path):
    with pdfplumber.open(path) as pdf:
        return pdf.pages[-1].extract_text() or ""


def _clean_block(text):
    """Remove page-number markers and copyright headers from a content block."""
    text = re.sub(r"[\-–—]{2,}\s*\d+\s*[\-–—]{2,}", " ", text)
    text = re.sub(r"【版權所有[^】]*】", " ", text)
    # Vertical 高點建國 header fragments
    text = re.sub(r"(?:高|點|建|國|•)\s*\n", "", text)
    text = re.sub(r"\d{2,3}\s*年.{0,30}高分詳解", " ", text)
    text = re.sub(r"《[^》]+》", " ", text)
    return re.sub(r" {2,}", " ", text).strip()


# ---------------------------------------------------------------------------
# Format 1: Old PDFs  (year <= 110)  —  answers embedded as （X）N
# ---------------------------------------------------------------------------

def _detect_old_format(path):
    """Return True if the PDF uses the embedded-answer 解析書 format （X）N."""
    with pdfplumber.open(path) as pdf:
        text = pdf.pages[0].extract_text() or ""
    return bool(re.search(r"（[ABCD]）\s*\d", text))


def parse_old_format(path):
    """
    Parse PDFs where answers appear as full-width （X）N at the start of each
    question line (解析書 format).  Also handles multi-select （ABCD）N.

    Fixes:
      • Markers only matched at line-start to avoid false hits in mid-sentence
        content like "硼（B）" or "α（A）".
      • Question number searched as the FIRST digit run in the next ~30 chars,
        so copyright noise "【75 下列..." is handled transparently.
    """
    text = _full_text(path)
    text = re.sub(r"[ \t]+", " ", text)

    # Match ALL full-width （X…）markers, then filter to those "near" line-start.
    # "Near" = the text before the marker on the same line is at most 3 ASCII
    # characters (handles subscript artifacts like "B（D）21" where the lone
    # "B" is a stray subscript from the previous line's "維生素B12").
    # Half-width content like "(A)硼（B）" is rejected because "(A)硼" is 4+ chars.
    # Also allow ＃ so "（＃）32" bonus markers are captured.
    raw_markers = list(re.finditer(r"（([ABCD＃]+)）", text))
    markers = []
    for rm in raw_markers:
        line_start = text.rfind("\n", 0, rm.start()) + 1
        prefix = text[line_start: rm.start()]
        # Accept if prefix is only whitespace + up to 3 ASCII word chars
        if re.match(r"^[\s0-9A-Za-z]{0,3}$", prefix):
            markers.append(rm)

    questions = []
    expected = 1

    for idx, m in enumerate(markers):
        # For multi-select answers, store all letters; single = one letter.
        answer_letters = m.group(1)
        after_raw = text[m.end():]

        # Find the first digit within the first 30 characters.
        # This skips over copyright noise like 【版權所有，翻印必究】 that may
        # appear between the answer marker and the question number.
        first_digit = re.search(r"\d", after_raw[:30])
        if not first_digit:
            continue
        dp = first_digit.start()          # offset of first digit in after_raw
        after = after_raw[dp:]            # view starting at first digit

        # Try 2-digit first, then 1-digit.  Using `expected` to resolve the
        # ambiguity of merged text like "420種" (Q4, content starts with "20").
        num = None
        content_offset = dp  # base offset (before the digits)
        for ndigits in [2, 1]:
            if len(after) >= ndigits and after[:ndigits].isdigit():
                candidate = int(after[:ndigits])
                if 1 <= candidate <= 80 and candidate == expected:
                    num = candidate
                    content_offset = dp + ndigits
                    break

        if num is None:
            continue

        # Content block: from after the number to the next answer marker
        block_end = markers[idx + 1].start() if idx + 1 < len(markers) else len(text)
        block = text[m.end() + content_offset: block_end]
        block = _clean_block(block)

        # Options use half-width  (A) (B) (C) (D)
        # Negative lookbehind prevents matching things like （A）inside content
        opt_ms = list(re.finditer(r"(?<![（A-Za-z])\(([ABCD])\)", block))
        if len(opt_ms) >= 4:
            content = block[: opt_ms[0].start()].strip()
            options = {}
            for i, om in enumerate(opt_ms[:4]):
                letter = om.group(1)
                opt_end = opt_ms[i + 1].start() if i + 1 < len(opt_ms) else len(block)
                raw = block[om.end(): opt_end]
                options[letter] = _clean_block(raw)
        else:
            content = block.strip()
            options = {"A": "", "B": "", "C": "", "D": ""}

        # Resolve ＃ answers: look in the next ~200 chars for "第N題答X給分"
        # Apply full-width → ASCII so Ａ/Ｂ/Ｃ/Ｄ are matched.
        if answer_letters == "＃":
            hint = text[m.end() + content_offset: m.end() + content_offset + 200].translate(FULLWIDTH)
            lm = re.search(r"答([ABCD])", hint)
            answer_letters = lm.group(1) if lm else ""

        questions.append({
            "number": num,
            "content": content,
            "has_image": False,
            "options": options,
            # Single-select: one letter.  Multi-select: all letters e.g. "ABCD".
            "answer": answer_letters,
            "bonus": False,
        })
        expected += 1

    return questions


# ---------------------------------------------------------------------------
# Format 2: New PDFs  (year >= 111)  —  official 考選部 format
# ---------------------------------------------------------------------------

def parse_new_format_questions(path):
    """
    Parse questions from official 考選部 PDFs.
    Questions are numbered 'N.' at line start; options use 'A.' format.
    """
    text = _full_text(path)
    text = re.sub(r"[ \t]+", " ", text)

    # Find question-number lines: digit(s) + period at line start (≤3 leading spaces)
    q_starts = []
    for m in re.finditer(r"(?:^|\n) {0,3}(\d{1,2})\.", text, re.MULTILINE):
        num = int(m.group(1))
        if 1 <= num <= 80:
            q_starts.append((m.start(), num))

    # Strict-incrementing filter
    filtered, expected = [], 1
    for pos, num in q_starts:
        if num == expected:
            filtered.append((pos, num))
            expected += 1
        elif expected < num <= expected + 2:
            filtered.append((pos, num))
            expected = num + 1

    questions = []
    for idx, (pos, num) in enumerate(filtered):
        end = filtered[idx + 1][0] if idx + 1 < len(filtered) else len(text)
        block = text[pos:end].strip()
        block = re.sub(r"^\d{1,2}\.\s*", "", block)

        # Options: 'A.' at line start (handles both 'A.' and '(A)' fallback)
        opt_ms = list(re.finditer(r"(?:^|\n) {0,4}([ABCD])\.", block, re.MULTILINE))
        if len(opt_ms) >= 4:
            content = block[: opt_ms[0].start()].strip()
            options = {}
            for i, om in enumerate(opt_ms[:4]):
                letter = om.group(1)
                opt_end = opt_ms[i + 1].start() if i + 1 < len(opt_ms) else len(block)
                options[letter] = block[om.end(): opt_end].strip()
        else:
            # Fallback: half-width (A) style
            opt_ms = list(re.finditer(r"(?<![（A-Za-z])\(([ABCD])\)", block))
            if len(opt_ms) >= 4:
                content = block[: opt_ms[0].start()].strip()
                options = {}
                for i, om in enumerate(opt_ms[:4]):
                    letter = om.group(1)
                    opt_end = opt_ms[i + 1].start() if i + 1 < len(opt_ms) else len(block)
                    options[letter] = block[om.end(): opt_end].strip()
            else:
                content = block.strip()
                options = {"A": "", "B": "", "C": "", "D": ""}

        questions.append({
            "number": num,
            "content": content,
            "has_image": False,
            "options": options,
            "answer": "",
            "bonus": False,
        })

    return questions


def parse_new_format_answers(path):
    """
    Parse the answer table from the last page of an official PDF.

    The last page looks like:
        題序 01 02 03 ... 20
        答案 Ａ Ｃ Ａ ... Ａ
        ...
        備 註：第16題，除未作答者不給分外，其餘均給分。...

    Returns dict  { question_number: answer_letter }
    Where answer_letter is 'A'–'D', or '' for fully-bonus questions.
    Bonus questions also set  bonus_set  (returned as second value).
    """
    text = _last_page_text(path).translate(FULLWIDTH)
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # ---- Parse footnote corrections -----------------------------------------
    # Collect all footnote text first (may span several lines)
    footnote_text = ""
    in_footnote = False
    for line in lines:
        if "備" in line and "註" in line:
            in_footnote = True
        if in_footnote:
            footnote_text += " " + line

    corrections = {}  # {q_num: 'A'/'B'/'C'/'D' or 'BONUS'}
    for m in re.finditer(r"第(\d{1,2})題", footnote_text):
        n = int(m.group(1))
        rest = footnote_text[m.end():]
        # "一律給分" or "除未作答者不給分外，其餘均給分" → everyone scores
        if "一律給分" in rest[:30] or ("均給分" in rest[:40] and "未作答" in rest[:40]):
            corrections[n] = "BONUS"
        elif "均給分" in rest[:60]:
            # "答A或B...均給分" → use first named letter
            lm = re.search(r"答([ABCD])", rest[:60])
            corrections[n] = lm.group(1) if lm else "BONUS"

    # ---- Parse answer rows ---------------------------------------------------
    answers = {}
    i = 0
    while i < len(lines):
        nums = re.findall(r"\b(\d{1,2})\b", lines[i])
        valid_nums = [n for n in nums if 1 <= int(n) <= 80]
        if len(valid_nums) >= 5 and i + 1 < len(lines):
            tokens = re.findall(r"([ABCD＃])", lines[i + 1])
            if len(tokens) >= len(valid_nums) - 2:
                for n, token in zip(valid_nums, tokens):
                    num = int(n)
                    if token == "＃":
                        corr = corrections.get(num, "A")
                        answers[num] = "" if corr == "BONUS" else corr
                    else:
                        answers[num] = token
                i += 2
                continue
        i += 1

    bonus_set = {n for n, corr in corrections.items() if corr == "BONUS"}
    return answers, bonus_set


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def convert_pdf(pdf_path, year):
    """Return (questions_list, bonus_set).

    Format is detected from PDF content, not year alone, because some official
    考選部 PDFs (without embedded answers) start as early as 104 年.
    """
    if _detect_old_format(pdf_path):
        questions = parse_old_format(pdf_path)
        return questions, set()
    else:
        questions = parse_new_format_questions(pdf_path)
        answers, bonus_set = parse_new_format_answers(pdf_path)
        for q in questions:
            n = q["number"]
            q["answer"] = answers.get(n, "")
            q["bonus"] = n in bonus_set
        return questions, bonus_set


def main():
    parser = argparse.ArgumentParser(description="Convert question PDFs to JSON")
    parser.add_argument("--subject", default=None, help="e.g. biochemistry")
    parser.add_argument("--year", type=int, default=None, help="Only this year")
    parser.add_argument("--force", action="store_true", help="Overwrite existing JSON")
    args = parser.parse_args()

    if args.subject:
        subject_dirs = [os.path.join(QUESTION_DIR, args.subject)]
    else:
        subject_dirs = [os.path.join(QUESTION_DIR, d) for d in CODE_TO_FOLDER.values()]

    total_ok = total_skip = 0
    errors = []

    for subject_dir in subject_dirs:
        folder = os.path.basename(subject_dir)
        code = FOLDER_TO_CODE.get(folder, "")
        subject_name = CODE_TO_SUBJECT_TW.get(code, folder)

        if not os.path.isdir(subject_dir):
            print(f"[SKIP] Not found: {subject_dir}")
            continue

        pdfs = sorted(
            f for f in os.listdir(subject_dir)
            if f.endswith(".pdf") and "answers" not in f
        )

        for pdf_name in pdfs:
            m = re.match(r"(\d{2,3})-(\d)-(\w+)\.pdf$", pdf_name)
            if not m:
                continue
            year, sitting, pdf_folder = int(m.group(1)), int(m.group(2)), m.group(3)

            if args.year and year != args.year:
                continue

            json_name = pdf_name.replace(".pdf", ".json")
            json_path = os.path.join(subject_dir, json_name)

            if os.path.exists(json_path) and not args.force:
                total_skip += 1
                print(f"  [SKIP] {folder}/{json_name}")
                continue

            pdf_path = os.path.join(subject_dir, pdf_name)
            print(f"  {folder}/{pdf_name} ... ", end="", flush=True)

            try:
                questions, bonus_set = convert_pdf(pdf_path, year)
                answered = sum(1 for q in questions if q["answer"])
                bonus_n = len(bonus_set)

                data = {
                    "exam_info": {
                        "year": year,
                        "sitting": sitting,
                        "subject": subject_name,
                        "exam_code": code,
                        "exam_type": "專技高考醫事檢驗師",
                        "duration_minutes": 60,
                        "total_questions": len(questions),
                    },
                    "questions": questions,
                }

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                print(f"OK  ({len(questions)} Qs, {answered} answered, {bonus_n} bonus)")
                total_ok += 1
            except Exception as e:
                print(f"ERROR: {e}")
                errors.append(f"{folder}/{pdf_name}: {e}")

    print(f"\n=== Summary ===")
    print(f"Converted : {total_ok}")
    print(f"Skipped   : {total_skip}")
    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  {e}")


if __name__ == "__main__":
    main()
