# -*- coding: utf-8 -*-
"""
批次 AI 知識點標籤分類
用法：
  python scripts/classify_tags.py                # 分類所有未標籤題目
  python scripts/classify_tags.py --limit 100    # 只分類 100 題（測試用）
  python scripts/classify_tags.py --subject-id 1 # 只分類指定科目
"""
import sys, json, time, asyncio, argparse, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from db.database import SessionLocal
from db.models import Question, Subject
from groq import AsyncGroq
from core.config import settings

BATCH_SIZE = 15     # 每次 API 請求送多少題（標籤輸出比難度長，縮小一點）
SLEEP_SECS = 2.5   # 請求間隔（Groq 免費版 30 req/min）
MODEL = "llama-3.1-8b-instant"  # 免費版 TPD 500K

_client = AsyncGroq(api_key=settings.groq_api_key)


class DailyLimitError(Exception):
    pass


_PROMPT = """你是醫檢師國考知識點分類專家。請為以下每道題目標記【知識點標籤】。
標籤規則：
- 使用繁體中文，每個標籤 4-12 個字
- 標籤代表這題直接考到的核心概念，不要描述題型
- 範例好標籤：「PCR原理」「革蘭氏染色」「腎絲球過濾率」「凝血因子活化」「肝臟酵素指標」
- 預設只給 1 個標籤；只有當題目明確同時考到兩個以上不同概念（例如需要同時理解兩種不同機制才能作答）才給 2-3 個
- 不確定要不要加第二個標籤時，就只給 1 個

輸入（JSON）：
{questions}

只輸出 JSON 陣列，格式如下，不要有任何其他文字：
[{{"idx": 0, "tags": ["標籤A", "標籤B"]}}, {{"idx": 1, "tags": ["標籤C"]}}]"""


async def classify_batch(questions: list[dict]) -> list[str | None]:
    q_list = []
    for i, q in enumerate(questions):
        q_list.append({
            "idx": i,
            "subject": q["subject"],
            "content": q["content"][:100],
            "A": q["option_a"][:35],
            "B": q["option_b"][:35],
        })

    prompt = _PROMPT.format(questions=json.dumps(q_list, ensure_ascii=False))

    for attempt in range(3):
        try:
            resp = await _client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            raw = resp.choices[0].message.content.strip()
            start, end = raw.find("["), raw.rfind("]") + 1
            if start == -1 or end == 0:
                return [None] * len(questions)
            results = json.loads(raw[start:end])
            output = [None] * len(questions)
            for r in results:
                idx = r.get("idx")
                tags = r.get("tags", [])
                if not isinstance(idx, int) or not (0 <= idx < len(questions)):
                    continue
                if not isinstance(tags, list) or not tags:
                    continue
                clean = [t.strip()[:15] for t in tags if isinstance(t, str) and t.strip()]
                if clean:
                    output[idx] = ",".join(clean[:3])
            return output
        except Exception as e:
            err_str = str(e)
            if "tokens per day" in err_str and "try again in" in err_str:
                raise DailyLimitError(err_str)
            # TPM 429：解析等待秒數後重試
            if "tokens per minute" in err_str or ("429" in err_str and "try again in" in err_str):
                m = re.search(r"try again in ([\d.]+)s", err_str)
                wait = float(m.group(1)) + 2 if m else 15
                print(f"\n  [TPM限制] 等待 {wait:.0f}s 後重試（第{attempt+1}次）...", end=" ", flush=True)
                time.sleep(wait)
                continue
            print(f"  [Error] {e}")
            return [None] * len(questions)
    return [None] * len(questions)


def _ensure_tags_column():
    """如果 questions.tags 欄位不存在，自動補上。"""
    from sqlalchemy import text
    from db.database import engine
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(questions)")).fetchall()]
        if "tags" not in cols:
            conn.execute(text("ALTER TABLE questions ADD COLUMN tags TEXT"))
            conn.commit()
            print("已自動新增 questions.tags 欄位\n")


async def main():
    _ensure_tags_column()
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="最多分類幾題（0=全部）")
    parser.add_argument("--subject-id", type=int, default=0, help="只分類指定 subject_id（0=全部）")
    parser.add_argument("--reclassify", action="store_true", help="清除現有標籤後重新分類")
    args = parser.parse_args()

    db = SessionLocal()

    if args.reclassify:
        target = db.query(Question)
        if args.subject_id:
            target = target.filter(Question.subject_id == args.subject_id)
        count = target.update({"tags": None})
        db.commit()
        print(f"已清除 {count} 題的標籤，重新分類中...\n")

    query = db.query(Question, Subject).join(Subject, Question.subject_id == Subject.id).filter(Question.tags == None)
    if args.subject_id:
        subj = db.query(Subject).filter(Subject.id == args.subject_id).first()
        query = query.filter(Question.subject_id == args.subject_id)
        print(f"科目篩選：{subj.name if subj else args.subject_id}")

    rows = query.all()
    if args.limit:
        rows = rows[:args.limit]

    total = len(rows)
    if total == 0:
        print("沒有需要標記的題目（全部已標記）")
        db.close()
        return

    print(f"待標記：{total} 題（每批 {BATCH_SIZE} 題，間隔 {SLEEP_SECS}s）")
    est_min = (total / BATCH_SIZE * SLEEP_SECS) / 60
    print(f"預估時間：{est_min:.1f} 分鐘\n")

    done = failed = 0
    for i in range(0, total, BATCH_SIZE):
        batch_rows = rows[i:i + BATCH_SIZE]
        batch_dicts = [
            {
                "content": q.content,
                "option_a": q.option_a,
                "option_b": q.option_b,
                "subject": s.name,
            }
            for q, s in batch_rows
        ]

        print(f"[{i+1}~{min(i+BATCH_SIZE, total)}/{total}]", end=" ", flush=True)
        try:
            tags_list = await classify_batch(batch_dicts)
        except DailyLimitError as e:
            db.commit()
            m = re.search(r"try again in (\d+)m([\d.]+)s", str(e))
            if m:
                wait_min = int(m.group(1))
                print(f"\n每日 token 額度已耗盡，請等待約 {wait_min} 分鐘後重跑腳本。")
                print(f"（台灣時間每天早上 8:00 重置，腳本會自動跳過已標記的 {done} 題）")
            else:
                print(f"\n每日 token 額度已耗盡，請明天再跑。已完成 {done} 題。")
            break

        fail_count = 0
        for (q, _), tags in zip(batch_rows, tags_list):
            if tags:
                q.tags = tags
                done += 1
            else:
                fail_count += 1
                failed += 1
        db.commit()

        print(f"ok={len(batch_rows)-fail_count}" + (f" fail={fail_count}" if fail_count else ""))

        if i + BATCH_SIZE < total:
            time.sleep(SLEEP_SECS)

    db.close()
    print(f"\n完成！成功={done}，失敗={failed}")
    if failed:
        print("提示：失敗題目的 tags 仍為 NULL，可重跑腳本補標記。")


if __name__ == "__main__":
    asyncio.run(main())
