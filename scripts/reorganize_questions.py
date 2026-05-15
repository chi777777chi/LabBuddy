# -*- coding: utf-8 -*-
import shutil, json
from pathlib import Path

root = Path(__file__).parent.parent / "Question"
src  = root / "臨床生理學與病理學"
dst  = root / "clinical_physiology"
dst.mkdir(exist_ok=True)

moves = [
    ("114-臨床生理學與病理學-1308.pdf",     "114-2-clinical_physiology.pdf"),
    ("114-臨床生理學與病理學-1308-解答.pdf", "114-2-clinical_physiology-answers.pdf"),
    ("114-2-臨床生理學與病理學.json",        "114-2-clinical_physiology.json"),
]
for old, new in moves:
    shutil.move(str(src / old), str(dst / new))
    print(f"moved: {old} -> {new}")

shutil.move(str(src / "images"), str(dst / "images"))
print("moved: images/")

shutil.rmtree(str(src))
print(f"removed: {src.name}/")

# 更新 JSON 裡的 image_path（路徑從中文改英文）
js = dst / "114-2-clinical_physiology.json"
data = json.loads(js.read_text(encoding="utf-8"))
for q in data["questions"]:
    if "image_path" in q:
        q["image_path"] = q["image_path"].replace("臨床生理學與病理學", "clinical_physiology")
js.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("updated image_path in JSON")

# 建立其餘 5 個科目資料夾
for s in ["hematology", "molecular_lab", "microbiology", "biochemistry", "immunology_virology"]:
    (root / s).mkdir(exist_ok=True)
    print(f"created: {s}/")

print("\nAll done.")
