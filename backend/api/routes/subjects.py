from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Subject

router = APIRouter(prefix="/subjects", tags=["subjects"])

SUBJECT_SEED = [
    {"name": "臨床生理學與病理學",         "name_en": "clinical_physiology",    "folder": "Question/clinical_physiology"},
    {"name": "臨床血液學與血庫學",          "name_en": "hematology",             "folder": "Question/hematology"},
    {"name": "醫學分子檢驗學與臨床鏡檢學", "name_en": "molecular_lab",          "folder": "Question/molecular_lab"},
    {"name": "微生物學與臨床微生物學",      "name_en": "microbiology",           "folder": "Question/microbiology"},
    {"name": "生物化學與臨床生化學",        "name_en": "biochemistry",           "folder": "Question/biochemistry"},
    {"name": "臨床血清免疫學與臨床病毒學",  "name_en": "immunology_virology",    "folder": "Question/immunology_virology"},
]


@router.get("/")
def list_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()


@router.post("/seed", summary="初始化六大科目（只需執行一次）")
def seed_subjects(db: Session = Depends(get_db)):
    added = []
    for s in SUBJECT_SEED:
        exists = db.query(Subject).filter(Subject.name_en == s["name_en"]).first()
        if not exists:
            db.add(Subject(**s))
            added.append(s["name_en"])
    db.commit()
    return {"added": added, "message": f"{len(added)} subjects seeded"}
