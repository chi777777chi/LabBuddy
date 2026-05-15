"""
把標準答案填入題庫 JSON 檔。
用法：python scripts/fill_answers.py
"""
import json
from pathlib import Path

ANSWERS = {
    1:"C",  2:"C",  3:"A",  4:"D",  5:"C",  6:"B",  7:"A",  8:"D",  9:"D", 10:"C",
   11:"D", 12:"B", 13:"D", 14:"A", 15:"A", 16:"C", 17:"A", 18:"B", 19:"C", 20:"C",
   21:"C", 22:"D", 23:"B", 24:"D", 25:"C", 26:"B", 27:"D", 28:"D", 29:"D", 30:"D",
   31:"A", 32:"C", 33:"C", 34:"B", 35:"C", 36:"A", 37:"C", 38:"A", 39:"C", 40:"B",
   41:"A", 42:"D", 43:"B", 44:"A", 45:"A", 46:"C", 47:"C", 48:"D", 49:"D", 50:"B",
   51:"D", 52:"A", 53:"B", 54:"B", 55:"D", 56:"A", 57:"C", 58:"D", 59:"A", 60:"A",
   61:"A", 62:"A", 63:"C", 64:"C", 65:"B", 66:"C", 67:"B", 68:"C", 69:"A", 70:"C",
   71:"C", 72:"D", 73:"C", 74:"D", 75:"D", 76:"B", 77:"A", 78:"A", 79:"C", 80:"D",
}

target = Path(__file__).parent.parent / "Question" / "臨床生理學與病理學" / "114-2-臨床生理學與病理學.json"

data = json.loads(target.read_text(encoding="utf-8"))
for q in data["questions"]:
    q["answer"] = ANSWERS[q["number"]]

target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✓ 已填入 {len(ANSWERS)} 題答案 → {target}")
