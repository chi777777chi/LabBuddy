# -*- coding: utf-8 -*-
"""
批次匯入考古題 JSON 至資料庫。
用法（在專案根目錄執行）：
    python scripts/import_questions.py
會自動掃描 Question/ 下所有 *.json，跳過已存在的題目。
"""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from db.database import SessionLocal, engine
from db.models import Base, Subject, Question

Base.metadata.create_all(bind=engine)

SUBJECT_MAP = {
    "clinical_physiology":   "臨床生理學與病理學",
    "hematology":            "臨床血液學與血庫學",
    "molecular_lab":         "醫學分子檢驗學與臨床鏡檢學",
    "microbiology":          "微生物學與臨床微生物學",
    "biochemistry":          "生物化學與臨床生化學",
    "immunology_virology":   "臨床血清免疫學與臨床病毒學",
}


def get_or_create_subject(db, name_en: str) -> Subject:
    subj = db.query(Subject).filter(Subject.name_en == name_en).first()
    if not subj:
        subj = Subject(
            name=SUBJECT_MAP[name_en],
            name_en=name_en,
            folder=f"Question/{name_en}",
        )
        db.add(subj)
        db.flush()
    return subj


def import_json(db, json_path: Path):
    data = json.loads(json_path.read_text(encoding="utf-8"))
    info = data["exam_info"]
    year, sitting = info["year"], info["sitting"]

    # 判斷科目（從資料夾名稱）
    name_en = json_path.parent.name
    if name_en not in SUBJECT_MAP:
        print(f"  [skip] unknown subject folder: {name_en}")
        return 0

    subject = get_or_create_subject(db, name_en)

    added = 0
    for q in data["questions"]:
        exists = db.query(Question).filter(
            Question.subject_id == subject.id,
            Question.year == year,
            Question.sitting == sitting,
            Question.number == q["number"],
        ).first()
        if exists:
            continue

        opts = q.get("options", {})
        db.add(Question(
            subject_id=subject.id,
            year=year,
            sitting=sitting,
            number=q["number"],
            content=q["content"],
            option_a=opts.get("A", ""),
            option_b=opts.get("B", ""),
            option_c=opts.get("C", ""),
            option_d=opts.get("D", ""),
            answer=q.get("answer") or "",
            has_image=q.get("has_image", False),
            image_path=q.get("image_path"),
        ))
        added += 1

    db.commit()
    return added


def main():
    root = Path(__file__).parent.parent / "Question"
    json_files = list(root.rglob("*.json"))

    if not json_files:
        print("No JSON files found in Question/")
        return

    db = SessionLocal()
    try:
        total = 0
        for jf in json_files:
            print(f"Importing: {jf.relative_to(root.parent)}")
            added = import_json(db, jf)
            print(f"  -> {added} questions added")
            total += added
        print(f"\nDone. Total added: {total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
