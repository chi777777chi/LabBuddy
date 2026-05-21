"""
classify_and_convert.py
将 Question/ 根目录的无名称 PDF 自动分类、移动、并转换成 JSON。

执行方式：
    cd <project_root>
    python scripts/classify_and_convert.py
"""

import json
import os
import re
import shutil

import pdfplumber

# 全形字母转 ASCII
FULLWIDTH = str.maketrans("ＡＢＣＤ", "ABCD")

# 科目对照表
CODE_TO_FOLDER = {
    "1308": "clinical_physiology",
    "2308": "hematology",
    "3308": "molecular_lab",
    "4308": "microbiology",
    "5308": "biochemistry",
    "6308": "immunology_virology",
}

CODE_TO_SUBJECT = {
    "1308": "临床生理学与病理学",
    "2308": "临床血液学与血库学",
    "3308": "医学分子检验学与临床镜检学",
    "4308": "微生物学与临床微生物学",
    "5308": "生物化学与临床生化学",
    "6308": "临床血清免疫学与临床病毒学",
}

# 使用繁体中文字串
CODE_TO_SUBJECT_TW = {
    "1308": "臨床生理學與病理學",
    "2308": "臨床血液學與血庫學",
    "3308": "醫學分子檢驗學與臨床鏡檢學",
    "4308": "微生物學與臨床微生物學",
    "5308": "生物化學與臨床生化學",
    "6308": "臨床血清免疫學與臨床病毒學",
}

QUESTION_DIR = os.path.join(os.path.dirname(__file__), "..", "Question")


def extract_first_page(path):
    with pdfplumber.open(path) as pdf:
        return pdf.pages[0].extract_text() or ""


def identify_pdf(text):
    """回传 (year, sitting, exam_code, is_answer)"""
    year_m = re.search(r"(\d{3})\s*年", text)
    year = int(year_m.group(1)) if year_m else 0

    sitting = 1 if "第一次" in text else (2 if "第二次" in text else 0)

    # 试题 PDF: "代 號：1308"；答案 PDF: "試題代號：3308)"
    code_m = re.search(r"代\s*[號号][：:（(]?\s*(\d{4})", text)
    exam_code = code_m.group(1) if code_m else ""

    # 答案卷识别：含「标准答案」
    is_answer = "標準答案" in text or "标准答案" in text

    return year, sitting, exam_code, is_answer


def extract_full_text(path):
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def parse_questions(text):
    """从试题 PDF 解析题目清单。"""
    # 正规化空白，但保留换行
    text = re.sub(r"[ \t]+", " ", text)

    # 找题号：出现在行首或换行后（数字1-80，后接句点，再接中文或英文内容）
    # 要求题号必须出现在空白/行首之后，且数字不能接在其他数字后
    q_starts = []
    for m in re.finditer(r"(?:^|\n) {0,3}(\d{1,2})\.", text, re.MULTILINE):
        num = int(m.group(1))
        if 1 <= num <= 80:
            q_starts.append((m.start(), num))

    # 确保题号严格递增（过滤掉误匹配）
    filtered = []
    expected = 1
    for pos, num in q_starts:
        if num == expected:
            filtered.append((pos, num))
            expected += 1
        elif num > expected and num <= expected + 2:
            # 允许少量跳号（PDF 分页或格式问题）
            filtered.append((pos, num))
            expected = num + 1

    questions = []
    for idx, (pos, num) in enumerate(filtered):
        end = filtered[idx + 1][0] if idx + 1 < len(filtered) else len(text)
        block = text[pos:end].strip()
        # 去掉开头题号
        block = re.sub(r"^\d{1,2}\.\s*", "", block)

        # 找选项 A. B. C. D.（前面不能是大写字母，避免误匹配缩写如 mRNA.）
        opt_matches = list(re.finditer(r"(?<![A-Za-z])([ABCD])\.", block))
        if len(opt_matches) >= 4:
            content = block[:opt_matches[0].start()].strip()
            options = {}
            for i, m in enumerate(opt_matches[:4]):
                letter = m.group(1)
                opt_end = opt_matches[i + 1].start() if i + 1 < len(opt_matches) else len(block)
                options[letter] = block[m.end():opt_end].strip()
        else:
            content = block.strip()
            options = {"A": "", "B": "", "C": "", "D": ""}

        questions.append({
            "number": num,
            "content": content,
            "has_image": False,
            "options": options,
            "answer": "",
        })

    return questions


def parse_answers(path):
    """从标准答案 PDF 解析题号→答案字母对照。"""
    text = extract_full_text(path).translate(FULLWIDTH)
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # 先从备注找「＃」更正答案：「第N题答X或Y者均给分」
    corrections = {}
    for line in lines:
        m = re.search(r"第(\d{1,2})題[^ABCD]*([ABCD])", line)
        if m and any(kw in line for kw in ("更正", "答", "給分")):
            corrections[int(m.group(1))] = m.group(2)

    answers = {}
    i = 0
    while i < len(lines):
        nums = re.findall(r"\b(\d{1,2})\b", lines[i])
        valid_nums = [n for n in nums if 1 <= int(n) <= 80]
        if len(valid_nums) >= 5 and i + 1 < len(lines):
            # 匹配 ABCD 和 ＃（更正符号）
            tokens = re.findall(r"([ABCD＃])", lines[i + 1])
            if len(tokens) >= len(valid_nums) - 2:
                for n, token in zip(valid_nums, tokens):
                    num = int(n)
                    if token == "＃":
                        answers[num] = corrections.get(num, "A")
                    else:
                        answers[num] = token
                i += 2
                continue
        i += 1

    return answers


def main():
    pdfs = [f for f in os.listdir(QUESTION_DIR)
            if f.endswith(".pdf") and f[0].isdigit()]

    print(f"Found {len(pdfs)} PDFs to classify\n")

    classified = []

    for pdf in sorted(pdfs):
        src = os.path.join(QUESTION_DIR, pdf)
        text = extract_first_page(src)
        year, sitting, code, is_answer = identify_pdf(text)

        folder = CODE_TO_FOLDER.get(code)
        if not folder or not year or not sitting:
            print(f"  [!] Cannot identify: {pdf} (year={year}, sitting={sitting}, code={code})")
            continue

        prefix = f"{year}-{sitting}-{folder}"
        suffix = "-answers" if is_answer else ""
        dest_name = f"{prefix}{suffix}.pdf"
        dest_dir = os.path.join(QUESTION_DIR, folder)
        dest = os.path.join(dest_dir, dest_name)

        kind = "answer" if is_answer else "questions"
        print(f"  {pdf} -> {folder}/{dest_name}  [{kind}]")
        classified.append((src, dest, dest_dir, year, sitting, code, is_answer, prefix))

    print()

    # 移动 PDF
    for src, dest, dest_dir, *_ in classified:
        os.makedirs(dest_dir, exist_ok=True)
        if os.path.exists(dest):
            print(f"  Already exists, skip: {os.path.basename(dest)}")
        else:
            shutil.move(src, dest)
            print(f"  Moved: {os.path.basename(dest)}")

    print()

    # 解析答案卷（扫描所有子目录，不限于本次移动的）
    answer_map = {}
    import glob
    for ans_pdf in glob.glob(os.path.join(QUESTION_DIR, "**", "*-answers.pdf"), recursive=True):
        name = os.path.basename(ans_pdf).replace("-answers.pdf", "")  # e.g. 114-1-molecular_lab
        ans = parse_answers(ans_pdf)
        answer_map[name] = ans
        print(f"  Parsed answers {name}: {len(ans)} questions")

    print()

    # 转换试题 PDF -> JSON（扫描所有子目录的试题 PDF）
    all_q_pdfs = [
        p for p in glob.glob(os.path.join(QUESTION_DIR, "**", "*.pdf"), recursive=True)
        if "answers" not in os.path.basename(p)
    ]
    for dest in all_q_pdfs:
        basename = os.path.basename(dest).replace(".pdf", "")  # e.g. 114-1-molecular_lab
        dest_dir = os.path.dirname(dest)

        # 解析 year/sitting/code from filename
        m = re.match(r"(\d{3})-(\d)-(\w+)", basename)
        if not m:
            continue
        year, sitting, folder = int(m.group(1)), int(m.group(2)), m.group(3)
        code = next((c for c, f in CODE_TO_FOLDER.items() if f == folder), "")
        prefix = basename

        json_path = os.path.join(dest_dir, f"{prefix}.json")
        if os.path.exists(json_path):
            print(f"  JSON exists, skip: {os.path.basename(json_path)}")
            continue

        print(f"  Parsing {prefix}...", end=" ", flush=True)
        text = extract_full_text(dest)
        questions = parse_questions(text)

        answers = answer_map.get(prefix, {})
        for q in questions:
            q["answer"] = answers.get(q["number"], "")

        data = {
            "exam_info": {
                "year": year,
                "sitting": sitting,
                "subject": CODE_TO_SUBJECT_TW.get(code, ""),
                "exam_code": code,
                "exam_type": "專技高考醫事檢驗師",
                "duration_minutes": 60,
                "total_questions": len(questions),
            },
            "questions": questions,
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        answered = sum(1 for q in questions if q["answer"])
        print(f"done ({len(questions)} questions, {answered} with answers)")

    # 清理临时文件
    for tmp in ["_test.txt", "_ans_test.txt"]:
        tmp_path = os.path.join(QUESTION_DIR, tmp)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    print("\nAll done!")


if __name__ == "__main__":
    main()
