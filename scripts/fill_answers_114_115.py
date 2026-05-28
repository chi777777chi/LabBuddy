# -*- coding: utf-8 -*-
"""
為 114、115 年題目填入標準答案。
答案來源：各科目資料夾內的 <year>-<sitting>-<subject>-answers.pdf

只更新 answer（和 bonus）欄位，其餘一律不動（content/options/image_path/difficulty/tags…）。

用法（在專案根目錄執行）：
    python scripts/fill_answers_114_115.py           # 預覽（dry-run）
    python scripts/fill_answers_114_115.py --apply   # 實際寫入 JSON + DB
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
sys.stdout.reconfigure(encoding="utf-8")

# reuse the existing parser from convert_questions_auto
sys.path.insert(0, str(Path(__file__).parent))
from convert_questions_auto import parse_new_format_answers

from db.database import SessionLocal
from db.models import Question, Subject

SUBJECT_MAP = {
    "clinical_physiology":   "臨床生理學與病理學",
    "hematology":            "臨床血液學與血庫學",
    "molecular_lab":         "醫學分子檢驗學與臨床鏡檢學",
    "microbiology":          "微生物學與臨床微生物學",
    "biochemistry":          "生物化學與臨床生化學",
    "immunology_virology":   "臨床血清免疫學與臨床病毒學",
}


def process_file(json_path: Path, apply: bool) -> dict:
    """
    Returns a summary dict with keys: subject, year, sitting, filled, errors.
    """
    data = json.loads(json_path.read_text(encoding="utf-8"))
    info = data["exam_info"]
    year, sitting = info["year"], info["sitting"]
    name_en = json_path.parent.name

    answers_pdf = json_path.with_name(json_path.stem + "-answers.pdf")
    if not answers_pdf.exists():
        return {"file": json_path.name, "error": f"找不到 {answers_pdf.name}"}

    answers, bonus_set = parse_new_format_answers(str(answers_pdf))
    if not answers:
        return {"file": json_path.name, "error": "答案 PDF 解析結果為空"}

    # ── 更新 JSON（only answer + bonus）──────────────────────────────
    changed_json = 0
    for q in data["questions"]:
        n = q["number"]
        new_ans = answers.get(n, "")
        new_bonus = n in bonus_set
        if q.get("answer") != new_ans or q.get("bonus") != new_bonus:
            q["answer"] = new_ans
            q["bonus"] = new_bonus
            changed_json += 1

    if apply and changed_json:
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 更新 DB（only answer 欄位）───────────────────────────────────
    changed_db = 0
    db = SessionLocal()
    try:
        subj = db.query(Subject).filter(Subject.name_en == name_en).first()
        if not subj:
            return {"file": json_path.name, "error": f"DB 找不到科目 {name_en}"}

        for q in data["questions"]:
            n = q["number"]
            new_ans = answers.get(n, "")
            record = db.query(Question).filter(
                Question.subject_id == subj.id,
                Question.year == year,
                Question.sitting == sitting,
                Question.number == n,
            ).first()
            if record and record.answer != new_ans:
                if apply:
                    record.answer = new_ans
                changed_db += 1

        if apply:
            db.commit()
    finally:
        db.close()

    return {
        "file": json_path.name,
        "year": year,
        "sitting": sitting,
        "answers_found": len(answers),
        "json_changes": changed_json,
        "db_changes": changed_db,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="實際寫入（不加此 flag 為 dry-run）")
    args = parser.parse_args()

    root = Path(__file__).parent.parent / "Question"
    target_jsons = []
    for f in sorted(root.rglob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        year = data["exam_info"]["year"]
        if year >= 114:
            target_jsons.append(f)

    if not target_jsons:
        print("找不到 114 年以上的 JSON 檔案")
        return

    mode = "【實際寫入】" if args.apply else "【Dry-run，不寫入】"
    print(f"{mode} 處理 {len(target_jsons)} 個檔案\n")

    for jf in target_jsons:
        result = process_file(jf, apply=args.apply)
        if "error" in result:
            print(f"  ✗ {result['file']}: {result['error']}")
        else:
            verb = "已更新" if args.apply else "待更新"
            print(
                f"  ✓ {result['file']}: "
                f"答案 {result['answers_found']} 題, "
                f"JSON {verb} {result['json_changes']} 題, "
                f"DB {verb} {result['db_changes']} 筆"
            )

    print("\n完成。" if args.apply else "\n如確認無誤，加上 --apply 參數執行。")


if __name__ == "__main__":
    main()
