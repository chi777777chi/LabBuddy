from groq import AsyncGroq
from core.config import settings

_client = AsyncGroq(api_key=settings.groq_api_key)

_PROMPTS = {
    1: """你是醫檢師國考的輔導老師。學生正在作答下面這題，請給出【第一層提示】。
規則：只用1句話，點出這題考的大方向領域，不提任何具體技術或方法名稱。

題目：{content}
選項：A. {option_a} / B. {option_b} / C. {option_c} / D. {option_d}

用繁體中文回答，只輸出提示句，不要加任何前綴說明。""",

    2: """你是醫檢師國考的輔導老師。學生正在作答下面這題，請給出【第二層提示】。
規則：用1-2句話，提示解題需要的核心概念或原理，可以提到相關物理/化學原理，但不要說出任何選項對應的技術名稱。

題目：{content}
選項：A. {option_a} / B. {option_b} / C. {option_c} / D. {option_d}

用繁體中文回答，只輸出提示句，不要加任何前綴說明。""",

    3: """你是醫檢師國考的輔導老師。學生正在作答下面這題，請給出【第三層提示】。
規則：用2-3句話，幾乎指向答案，可以描述正確答案的關鍵特徵或定義，但不要直接說「答案是X」或點名選項字母。

題目：{content}
選項：A. {option_a} / B. {option_b} / C. {option_c} / D. {option_d}

用繁體中文回答，只輸出提示句，不要加任何前綴說明。""",
}


_WEAKNESS_PROMPT = """你是醫檢師國考的學習顧問。以下是學生的答題統計數據，請根據這些數據給出具體的學習建議。

【各科答對率】
{subject_stats}

【最近考試趨勢】
{score_trend}

【最常答錯的題目】
{weak_questions}

【作答時間效率】
{time_stats}

【最耗時的知識點（平均答題秒數最高）】
{slow_tags}

請用繁體中文回答，依以下五個段落輸出，每段開頭用「◆ 標題」標示，內容2-4句，不要使用任何 Markdown 符號（不要用 ** # - 等）：

◆ 弱點科目分析
（指出答對率最低的1-2科，說明需要加強的方向）

◆ 成績趨勢觀察
（觀察近期考試分數是進步、退步還是持平，給出看法）

◆ 重點複習建議
（針對最常答錯的題目，給出具體的複習策略）

◆ 作答速度分析
（根據平均答題時間與國考標準75秒/題比較，以及最耗時的知識點，給出具體建議；若無時間數據，跳過此段）

◆ 備考行動建議
（給出1-2個這週可以立刻執行的具體行動）"""


async def get_weakness_analysis_with_time(
    subject_stats: list[dict],
    score_trend: list[dict],
    weak_questions: list[dict],
    time_stats: dict | None = None,
    slow_tags: list[dict] | None = None,
) -> str:
    # 格式化科目統計
    subj_lines = []
    for s in subject_stats:
        if s["accuracy_rate"] is not None:
            subj_lines.append(f"  - {s['subject_name']}：答對率 {s['accuracy_rate']}%（{s['correct_count']}/{s['total_answered']} 題）")
        else:
            subj_lines.append(f"  - {s['subject_name']}：尚無作答記錄")

    # 格式化成績趨勢
    if score_trend:
        trend_lines = [f"  - {t['date']} {t['subject_name']}：{t['score']}/{t['total']}（{t['percentage']}%）" for t in score_trend[-10:]]
    else:
        trend_lines = ["  - 尚無考試記錄"]

    # 格式化弱點題目
    if weak_questions:
        weak_lines = [f"  - [{w['subject_name']} {w['source']}] 答錯{w['wrong_count']}次：{w['content']}" for w in weak_questions[:5]]
    else:
        weak_lines = ["  - 尚無答錯記錄"]

    # 格式化時間效率
    if time_stats and time_stats.get("has_data"):
        avg = time_stats["avg_time_seconds"]
        expected = time_stats["expected_time_seconds"]
        ratio = time_stats["speed_ratio"]
        speed_label = "偏慢" if ratio > 1.3 else ("偏快" if ratio < 0.5 else "適中")
        time_lines = [
            f"  - 平均每題用時：{avg} 秒（國考標準：{expected} 秒/題）",
            f"  - 速度評估：{speed_label}（實際/標準 = {ratio}）",
            f"  - 超過120秒的慢題：{time_stats['slow_count']} 題，低於20秒的快題：{time_stats['fast_count']} 題",
            f"  - 統計樣本：{time_stats['total_answered_with_time']} 題",
        ]
    else:
        time_lines = ["  - 尚無作答時間記錄（需完成至少一場計時練習）"]

    if slow_tags:
        slow_tag_lines = [
            f"  - {t['tag']}：平均 {t['avg_seconds']} 秒/題（共 {t['count']} 題）"
            for t in slow_tags[:5]
        ]
    else:
        slow_tag_lines = ["  - 尚無知識點時間統計（需完成計時練習且題目已標記標籤）"]

    prompt = _WEAKNESS_PROMPT.format(
        subject_stats="\n".join(subj_lines),
        score_trend="\n".join(trend_lines),
        weak_questions="\n".join(weak_lines),
        time_stats="\n".join(time_lines),
        slow_tags="\n".join(slow_tag_lines),
    )
    response = await _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


async def get_hint(content: str, option_a: str, option_b: str, option_c: str, option_d: str, level: int = 1) -> str:
    prompt = _PROMPTS.get(level, _PROMPTS[3]).format(
        content=content,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
    )
    response = await _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
