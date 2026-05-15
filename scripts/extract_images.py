"""
從試卷 PDF 中擷取圖片，存入 Question/images/ 資料夾，
並更新對應 JSON 的 image_path 欄位。

用法：python scripts/extract_images.py <pdf路徑> <json路徑>
範例：
  python scripts/extract_images.py \
    "Question/clinical_physiology/114-2-clinical_physiology.json"
"""
import fitz  # PyMuPDF
import json
import sys
from pathlib import Path

SUBJECT_MAP = {
    "臨床生理學與病理學": "clinical_physiology",
    "臨床血液學與血庫學": "hematology",
    "醫學分子檢驗學與臨床鏡檢學": "molecular_lab",
    "微生物學與臨床微生物學": "microbiology",
    "生物化學與臨床生化學": "biochemistry",
    "臨床血清免疫學與臨床病毒學": "immunology_virology",
}

def extract_images(pdf_path: Path, json_path: Path):
    data = json.loads(json_path.read_text(encoding="utf-8"))
    info = data["exam_info"]
    subject_en = SUBJECT_MAP.get(info["subject"], "unknown")
    prefix = f"{info['year']}-{info['sitting']}-{subject_en}"

    out_dir = json_path.parent / "images"
    out_dir.mkdir(exist_ok=True)

    doc = fitz.open(pdf_path)
    saved = {}
    img_idx = 0

    for page_num, page in enumerate(doc):
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            base_img = doc.extract_image(xref)
            ext = base_img["ext"]
            img_bytes = base_img["image"]

            img_idx += 1
            filename = f"{prefix}-img{img_idx:02d}.{ext}"
            out_path = out_dir / filename
            out_path.write_bytes(img_bytes)
            saved[img_idx] = str(out_path.relative_to(json_path.parent.parent.parent))
            print(f"  [p{page_num+1}] {filename}")

    doc.close()
    print(f"\n共擷取 {img_idx} 張圖片")
    print("請對照題目手動將 image_path 填入 JSON 的對應題號")
    print("有圖片的題號：", [q["number"] for q in data["questions"] if q.get("has_image")])
    print("\n圖片順序參考：")
    for k, v in saved.items():
        print(f"  img{k:02d} -> {v}")

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    # 預設路徑（可改為 sys.argv）
    pdf = root / "Question" / "臨床生理學與病理學" / "114-臨床生理學與病理學-1308.pdf"
    js  = root / "Question" / "臨床生理學與病理學" / "114-2-臨床生理學與病理學.json"
    extract_images(pdf, js)
