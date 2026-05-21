# AddingQuestions.md — 新增題庫操作指南

> 說明新增考古題時，前後端需要做哪些事。
> 短答：**通常不需要改程式碼**，只需要跑兩個腳本。

---

## 快速流程（一般情況）

```
1. 下載 PDF 放進 Question/
2. python scripts/classify_and_convert.py   ← 分類 + 產生 JSON
3. python scripts/import_questions.py        ← 匯入 DB
4. 重啟後端（uvicorn）                       ← 讓新資料生效
```

前端不需要修改，選單會自動從 DB 讀取可用的年份／梯次。

---

## 詳細說明

### 步驟 1：取得 PDF

從考選部網站（https://www.moex.gov.tw）下載：
- **試題 PDF**：考試試題（含 A/B/C/D 選項）
- **標準答案 PDF**：對應的答案卷

兩個 PDF 都需要，否則題目會沒有答案。

下載後放進 `Question/` 根目錄（檔名不重要，腳本會自動識別）。

### 步驟 2：執行分類腳本

```bash
cd <project_root>
python scripts/classify_and_convert.py
```

會自動：
- 識別科目、年份、梯次、類型
- 移動並重命名檔案到對應子目錄
- 產生 `.json` 題庫檔

詳細規則見 `docs/QuestionBank.md`。

### 步驟 3：匯入資料庫

```bash
python scripts/import_questions.py
```

- 掃描 `Question/` 所有 `.json`，新題目直接寫入 DB
- 已存在的題目自動跳過（不會重複）

### 步驟 4：重啟後端

```bash
# 停止目前的 uvicorn，再重啟
cd backend
uvicorn main:app --reload
```

如果後端已在跑 `--reload` 模式，修改 `.json` 不會觸發重載，但 DB 匯入後重啟一次可確保乾淨。

---

## 前端是否需要修改？

**通常不需要。** 前端年份／梯次選單是動態從 API 讀取：

```
GET /questions/exams/list?subject_id={id}
→ 回傳 DB 中所有 (year, sitting) 組合
→ 前端自動渲染成「114年第一次」「115年第一次」...
```

只要題目成功進 DB，選單就會自動出現新選項。

---

## 需要改程式碼的情況

| 情況 | 需要改哪裡 |
|------|-----------|
| 新增**新科目**（目前 6 科以外） | 見下方「新增科目」 |
| 題目格式有重大差異（PDF 結構改變） | `scripts/classify_and_convert.py` → `parse_questions()` |
| 答案格式改變（非 Ａ Ｂ Ｃ Ｄ） | `scripts/classify_and_convert.py` → `parse_answers()` |

---

## 新增科目（擴充現有 6 科）

若考選部新增科目，需要以下修改：

### 1. `scripts/classify_and_convert.py`

在 `CODE_TO_FOLDER` 和 `CODE_TO_SUBJECT_TW` 加入新科目：

```python
CODE_TO_FOLDER = {
    ...
    "7308": "new_subject",   # 新科目代號 → 資料夾名稱
}

CODE_TO_SUBJECT_TW = {
    ...
    "7308": "新科目中文名稱",
}
```

### 2. `scripts/import_questions.py`

在 `SUBJECT_MAP` 加入新科目：

```python
SUBJECT_MAP = {
    ...
    "new_subject": "新科目中文名稱",
}
```

### 3. 建立資料夾

```bash
mkdir Question/new_subject
```

### 4. 後端（DB）

後端的 `Subject` 表由 `import_questions.py` 自動建立，不需要手動修改 schema 或 migration。

---

## 常見問題

### Q：腳本說「Cannot identify」怎麼辦？

```
[!] Cannot identify: xxxxx.pdf (year=0, sitting=1, code=6308)
```

代表 year 解析失敗。通常是 PDF 標頭的年份格式特殊（如 `115 年` 有空格），或是非標準考選部 PDF。

**解法**：手動重新命名後放入對應資料夾：
```bash
# 直接放進去，跳過腳本
cp xxxxx.pdf Question/clinical_physiology/115-2-clinical_physiology.pdf
```

然後直接對這個檔案跑 parse_questions 和 parse_answers，或手動建立 JSON。

---

### Q：JSON 裡有些題目選項是空的

部分題目有圖片（`has_image: true`），文字選項可能為空或不完整。目前系統不支援圖片題的自動提取，需要手動補充：

1. 打開對應的 `.json` 檔
2. 找到 `has_image: false` 但選項為空的題目
3. 手動填入 `option_a` ~ `option_d`
4. 將 `has_image` 改為 `true`（若確實有圖片）
5. 重跑 `import_questions.py`（會跳過已存在的題目，需先刪除 DB 中該題再重跑，或直接 UPDATE）

---

### Q：答案全部是空的

代表找不到對應的答案 PDF，或答案 PDF 尚未放入 `Question/`。

確認：
- 答案 PDF 的檔名是 `{year}-{sitting}-{subject}-answers.pdf`
- 試題 PDF 的 prefix 和答案 PDF 的 prefix 完全一致

---

### Q：匯入後後端 API 沒有新年份

確認：
1. `import_questions.py` 有輸出 `-> N questions added`（N > 0）
2. 後端已重啟
3. 呼叫 `GET /questions/exams/list?subject_id=X` 確認回傳新年份

---

## 檔案對照總覽

| 檔案 | 用途 |
|------|------|
| `scripts/classify_and_convert.py` | PDF 分類、命名、轉 JSON |
| `scripts/import_questions.py` | JSON → SQLite DB |
| `backend/api/routes/questions.py` | 提供 `/questions/exams/list` API |
| `frontend/app/state/exam_state.py` | `load_available_exams()` 呼叫 API，`set_exam()` 設定選擇 |
| `frontend/app/pages/exam_setup.py` | 年份／梯次下拉選單 UI |
| `docs/QuestionBank.md` | PDF 分類規則與踩坑紀錄 |
