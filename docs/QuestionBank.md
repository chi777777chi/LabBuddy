# QuestionBank.md — 題庫管理指南

> 本文件記錄題庫 PDF 的分類規則、命名慣例、轉換流程，以及過去遇到的問題與解法。
> 新增考古題前請先閱讀本文件。

---

## 目錄結構

```
Question/
├── clinical_physiology/       # 臨床生理學與病理學
├── hematology/                # 臨床血液學與血庫學
├── molecular_lab/             # 醫學分子檢驗學與臨床鏡檢學
├── microbiology/              # 微生物學與臨床微生物學
├── biochemistry/              # 生物化學與臨床生化學
└── immunology_virology/       # 臨床血清免疫學與臨床病毒學
```

---

## 科目識別（試題代號對照）

考選部的 PDF 標頭會標示試題代號，對應科目如下：

| 試題代號 | 科目名稱（中） | 資料夾名稱 |
|---------|--------------|-----------|
| 1308 | 臨床生理學與病理學 | `clinical_physiology` |
| 2308 | 臨床血液學與血庫學 | `hematology` |
| 3308 | 醫學分子檢驗學與臨床鏡檢學 | `molecular_lab` |
| 4308 | 微生物學與臨床微生物學 | `microbiology` |
| 5308 | 生物化學與臨床生化學 | `biochemistry` |
| 6308 | 臨床血清免疫學與臨床病毒學 | `immunology_virology` |

**識別方式**：PDF 第一頁會有以下格式：
- 試題 PDF：`代 號：1308`
- 答案 PDF：`科目名稱：...(試題代號：1308)`

---

## 檔案命名規則

```
{年份}-{梯次}-{資料夾名稱}.pdf        ← 試題
{年份}-{梯次}-{資料夾名稱}-answers.pdf ← 標準答案
{年份}-{梯次}-{資料夾名稱}.json        ← 轉換後題庫（程式自動產生）
```

**範例：**
```
114-1-clinical_physiology.pdf
114-1-clinical_physiology-answers.pdf
114-1-clinical_physiology.json
```

- 年份：民國年（例：114、115）
- 梯次：`1` = 第一次，`2` = 第二次

---

## 如何辨別試題 PDF vs 答案 PDF

| 特徵 | 試題 PDF | 答案 PDF |
|------|---------|---------|
| 第一頁開頭 | `114年第一次...` | `測驗式試題標準答案` 或 `測驗題標準答案更正` |
| 包含 | A/B/C/D 選項內容 | 題號＋答案字母的表格 |
| 是否有 `標準答案` 字樣 | 否 | **是**（用來識別） |

---

## 轉換流程

### 步驟 1：下載 PDF 放進 `Question/`

從考選部網站下載的 PDF 通常是亂碼數字命名（如 `353552573.pdf`），直接放進 `Question/` 根目錄即可。

### 步驟 2：執行分類轉換腳本

```bash
cd <project_root>
python scripts/classify_and_convert.py
```

腳本會自動：
1. 識別每個 PDF 的年份、梯次、科目、類型（試題/答案）
2. 移動並重新命名到對應子目錄
3. 解析答案 PDF 的答案對照表
4. 解析試題 PDF 的每道題目（題號、內容、選項 A-D）
5. 將題目和答案合併，輸出 `.json` 檔

### 步驟 3：匯入資料庫

```bash
cd <project_root>
python scripts/import_questions.py
```

腳本會掃描 `Question/` 下所有 `.json`，跳過已存在的題目（以科目+年份+梯次+題號為唯一鍵）。

---

## 已知困難與解法

### 1. 年份格式不一致（`115 年` vs `114年`）

**問題：** 部分 PDF（尤其是 115 年）在年份後有空格，如 `115 年第一次`。

**影響：** 正規表達式 `(\d{3})年` 無法匹配。

**解法：** 改為 `(\d{3})\s*年`，允許年份和「年」字之間有零或多個空白。

---

### 2. 答案字母為全形（Ａ Ｂ Ｃ Ｄ）

**問題：** 考選部的答案 PDF 使用全形字母 Ａ Ｂ Ｃ Ｄ，而非 ASCII A B C D。

**影響：** 正則 `[ABCD]` 無法匹配。

**解法：** 在解析前先用 `str.translate` 將全形轉換：
```python
FULLWIDTH = str.maketrans("ＡＢＣＤ", "ABCD")
text = text.translate(FULLWIDTH)
```

---

### 3. 答案更正卷（`＃` 符號）

**問題：** 部分考古題有更正版答案卷（標題含「更正」），更正的題目答案欄位標記為 `＃`（全形 #），代表「多個選項皆可得分，詳見備註」。

**影響：** `＃` 不是 ABCD，被 parser 跳過；由於佔用了一個位置卻沒有被計入，後面所有答案往前位移一格，導致最後一題（第 40/60/80 題）沒有答案。

**解法：**
1. 在正規表達式加入 `＃` 為有效 token：`re.findall(r"([ABCD＃])", answer_line)`
2. 遇到 `＃` 時，從備註行（「第N題答X或Y者均給分」）取第一個有效字母作為答案

```python
# 預先從備註解析更正答案
corrections = {}
for line in lines:
    m = re.search(r"第(\d{1,2})題[^ABCD]*([ABCD])", line)
    if m and any(kw in line for kw in ("更正", "答", "給分")):
        corrections[int(m.group(1))] = m.group(2)

# 解析答案行時處理 ＃
for n, token in zip(valid_nums, tokens):
    if token == "＃":
        answers[int(n)] = corrections.get(int(n), "A")
    else:
        answers[int(n)] = token
```

---

### 4. Terminal 顯示亂碼

**問題：** 在 Windows 終端機直接 `print()` 中文內容會顯示亂碼（CP950 編碼問題）。

**影響：** 乍看以為文字提取失敗，實際上是顯示問題。

**診斷方式：** 將文字寫入 UTF-8 檔案再讀取：
```python
with open("_debug.txt", "w", encoding="utf-8") as f:
    f.write(text)
```

**結論：** pdfplumber 提取的文字是正確 Unicode，只是 Terminal 無法顯示。

---

### 5. 題號 Parser 誤抓內容中的數字

**問題：** 題目內容中出現數字（如選項 `A.30 mm`、百分比 `5.6%`）被誤認為題號。

**影響：** 同一份考卷被解析出 85-91 道題，多於實際的 80 題。

**解法：**
1. 使用 `re.MULTILINE` 模式，限制題號只能出現在行首（`(?:^|\n) {0,3}(\d{1,2})\.`）
2. 加入遞增驗證：題號必須嚴格遞增，不符合的忽略

```python
q_starts = []
for m in re.finditer(r"(?:^|\n) {0,3}(\d{1,2})\.", text, re.MULTILINE):
    num = int(m.group(1))
    if 1 <= num <= 80:
        q_starts.append((m.start(), num))

# 確保嚴格遞增
filtered = []
expected = 1
for pos, num in q_starts:
    if num == expected:
        filtered.append((pos, num))
        expected += 1
```

---

## 注意事項

- **答案更正卷**：若考選部發布了更正版答案（標題有「更正」），腳本會以更正版為準。
- **圖片題**：含圖片的題目目前 `has_image` 仍設為 `False`，因為圖片無法從 PDF 自動提取，需手動補充。
- **重複匯入保護**：`import_questions.py` 以「科目＋年份＋梯次＋題號」為唯一鍵，重複執行不會產生重複題目。
- **114-2 題庫**：原始 JSON 由人工整理，是最乾淨的參考版本，勿覆蓋。
