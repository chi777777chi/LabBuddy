# -*- coding: utf-8 -*-
"""
批次 AI 難易度分類（easy / medium / hard）
用法：
  python scripts/classify_difficulty.py                # 分類所有未分類題目
  python scripts/classify_difficulty.py --limit 100    # 只分類 100 題（測試用）
  python scripts/classify_difficulty.py --subject-id 1 # 只分類指定科目
"""
import sys, json, time, asyncio, argparse, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from db.database import SessionLocal
from db.models import Question, Subject
from groq import AsyncGroq
from core.config import settings

BATCH_SIZE = 20      # 每次 API 請求送多少題
SLEEP_SECS = 2.5    # 請求間隔（Groq 免費版 30 req/min）
MODEL = "llama-3.1-8b-instant"  # 免費版 TPD 500K（70B 只有 100K）

_client = AsyncGroq(api_key=settings.groq_api_key)


class DailyLimitError(Exception):
    pass

_PROMPT = """你是醫檢師國考題目難度分類專家。請判斷以下每道題目的難度：
- easy（簡單）：考基本定義、直接記憶、教科書常識
- medium（中等）：需理解概念、比較分析、基本計算
- hard（困難）：複雜計算、罕見知識、多步驟推理

輸入（JSON）：
{questions}

只輸出 JSON 陣列，格式如下，不要有任何其他文字：
[{{"idx": 0, "difficulty": "easy"}}, {{"idx": 1, "difficulty": "medium"}}, ...]"""


async def classify_batch(questions: list[dict]) -> list[str | None]:
    q_list = []
    for i, q in enumerate(questions):
        q_list.append({
            "idx": i,
            "content": q["content"][:120],
            "A": q["option_a"][:40],
            "B": q["option_b"][:40],
            "C": q["option_c"][:40],
            "D": q["option_d"][:40],
        })

    prompt = _PROMPT.format(questions=json.dumps(q_list, ensure_ascii=False))

    try:
        resp = await _client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        raw = resp.choices[0].message.content.strip()
        start, end = raw.find("["), raw.rfind("]") + 1
        if start == -1 or end == 0:
            return [None] * len(questions)
        results = json.loads(raw[start:end])
        output = [None] * len(questions)
        for r in results:
            idx = r.get("idx")
            diff = str(r.get("difficulty", "")).lower()
            if isinstance(idx, int) and 0 <= idx < len(questions) and diff in ("easy", "medium", "hard"):
                output[idx] = diff
        return output
    except Exception as e:
        err_str = str(e)
        # 日額度耗盡：解析等待時間並拋出特殊例外
        if "tokens per day" in err_str and "try again in" in err_str:
            raise DailyLimitError(err_str)
        print(f"  [Error] {e}")
        return [None] * len(questions)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="最多分類幾題（0=全部）")
    parser.add_argument("--subject-id", type=int, default=0, help="只分類指定 subject_id（0=全部）")
    args = parser.parse_args()

    db = SessionLocal()
    query = db.query(Question).filter(Question.difficulty == None)
    if args.subject_id:
        subj = db.query(Subject).filter(Subject.id == args.subject_id).first()
        query = query.filter(Question.subject_id == args.subject_id)
        print(f"科目篩選：{subj.name if subj else args.subject_id}")

    questions = query.all()
    if args.limit:
        questions = questions[:args.limit]

    total = len(questions)
    if total == 0:
        print("沒有需要分類的題目（全部已分類）")
        db.close()
        return

    print(f"待分類：{total} 題（每批 {BATCH_SIZE} 題，間隔 {SLEEP_SECS}s）")
    est_min = (total / BATCH_SIZE * SLEEP_SECS) / 60
    print(f"預估時間：{est_min:.1f} 分鐘\n")

    done = failed = 0
    for i in range(0, total, BATCH_SIZE):
        batch_qs = questions[i:i + BATCH_SIZE]
        batch_dicts = [
            {"content": q.content, "option_a": q.option_a,
             "option_b": q.option_b, "option_c": q.option_c, "option_d": q.option_d}
            for q in batch_qs
        ]

        print(f"[{i+1}~{min(i+BATCH_SIZE, total)}/{total}]", end=" ", flush=True)
        try:
            difficulties = await classify_batch(batch_dicts)
        except DailyLimitError as e:
            db.commit()
            # 從錯誤訊息解析等待時間
            m = re.search(r"try again in (\d+)m([\d.]+)s", str(e))
            if m:
                wait_min = int(m.group(1))
                print(f"\n每日 token 額度已耗盡，請等待約 {wait_min} 分鐘後重跑腳本。")
                print(f"（台灣時間每天早上 8:00 重置，腳本會自動跳過已分類的 {done} 題）")
            else:
                print(f"\n每日 token 額度已耗盡，請明天再跑。已完成 {done} 題。")
            break

        counts = {"easy": 0, "medium": 0, "hard": 0, "fail": 0}
        for q, diff in zip(batch_qs, difficulties):
            if diff:
                q.difficulty = diff
                counts[diff] += 1
                done += 1
            else:
                counts["fail"] += 1
                failed += 1
        db.commit()

        print(f"easy={counts['easy']} medium={counts['medium']} hard={counts['hard']}"
              + (f" fail={counts['fail']}" if counts["fail"] else ""))

        if i + BATCH_SIZE < total:
            time.sleep(SLEEP_SECS)

    db.close()
    print(f"\n完成！成功={done}，失敗={failed}")
    if failed:
        print("提示：失敗題目的 difficulty 仍為 NULL，可重跑腳本補分類。")


if __name__ == "__main__":
    asyncio.run(main())
