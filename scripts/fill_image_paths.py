"""把擷取好的圖片路徑填入 JSON 對應題號。"""
import json
from pathlib import Path

root = Path(__file__).parent.parent
js = root / "Question" / "臨床生理學與病理學" / "114-2-臨床生理學與病理學.json"

IMG_BASE = "Question/臨床生理學與病理學/images"
IMAGE_MAP = {
    1:  f"{IMG_BASE}/114-2-clinical_physiology-img01.png",
    4:  f"{IMG_BASE}/114-2-clinical_physiology-img02.jpeg",
    7:  f"{IMG_BASE}/114-2-clinical_physiology-img03.jpeg",
    9:  f"{IMG_BASE}/114-2-clinical_physiology-img04.jpeg",
    26: f"{IMG_BASE}/114-2-clinical_physiology-img05.jpeg",
    31: f"{IMG_BASE}/114-2-clinical_physiology-img06.jpeg",
    32: f"{IMG_BASE}/114-2-clinical_physiology-img07.jpeg",
}

data = json.loads(js.read_text(encoding="utf-8"))
for q in data["questions"]:
    if q["number"] in IMAGE_MAP:
        q["image_path"] = IMAGE_MAP[q["number"]]

js.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("image_path filled for questions:", list(IMAGE_MAP.keys()))
