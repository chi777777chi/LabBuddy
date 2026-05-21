# 醫檢師國考線上題庫平台

台灣醫事檢驗師國家考試的線上練習平台，支援六大科目考古題練習、AI 分析回饋與多角色權限管理。

## 功能特色

### 已完成（學生端）
- Google OAuth 登入
- 六大科目考古題練習（96–115 年，5 / 10 / 80 題）
- 出題模式：單份完整、單份隨機、多份隨機、選項順序隨機
- 計時模式（每題 90 秒，< 30 秒變紅，時間到自動交卷）
- 刪去法輔助答題
- 即時對答 / 模擬考模式切換
- 成績頁、歷史紀錄、錯題複習
- PDF 匯出（答題記錄含對錯標色）
- **AI 分階段提示**（答題中 3 層遞進提示，由 Groq AI 生成）
- **AI 弱點分析頁**（各科答對率、成績趨勢折線圖、最常答錯題目、AI 學習建議）
- **個人資料頁**（學習統計、快速導航）

### 規劃中
- 老師端（班級管理、學生進度監控）
- 管理員端（使用者管理、題庫維護）

## 考試科目

| # | 科目 |
|---|------|
| 1 | 臨床生理學與病理學 |
| 2 | 臨床血液學與血庫學 |
| 3 | 醫學分子檢驗學與臨床鏡檢學 |
| 4 | 微生物學與臨床微生物學 |
| 5 | 生物化學與臨床生化學 |
| 6 | 臨床血清免疫學與臨床病毒學 |

> 每年兩次考試，目前收錄 96–115 年考古題。

## 技術架構

| 層級 | 技術 |
|------|------|
| 後端 | FastAPI (Python 3.10+) |
| 前端 | Reflex 0.9（純 Python，編譯為 React） |
| AI | Groq API（llama-3.3-70b-versatile） |
| 認證 | Google OAuth 2.0 |
| 資料庫 | SQLite（開發 / 本地部署） |

## 專案結構

```
├── backend/
│   ├── api/routes/       # auth, users, subjects, questions, exam, ai, analytics
│   ├── core/             # 設定、JWT 安全性
│   ├── db/               # SQLAlchemy models + database
│   ├── services/         # ai_service（Groq hint + weakness analysis）
│   └── utils/            # PDF 匯出
├── frontend/
│   └── app/
│       ├── pages/        # login, home, exam_setup, exam, result, history,
│       │                 # wrong_review, analytics, profile
│       └── state/        # auth, exam, analytics, profile states
├── scripts/
│   ├── import_questions.py   # 批次匯入 JSON 至資料庫
│   └── gen_test_token.py     # 產生測試用 JWT
├── Question/             # 各科目考古題 JSON（96–115 年）
└── docs/                 # 規格文件
```

## 快速開始

### 環境需求
- Python 3.10+
- Node.js 18+（Reflex 編譯用）

### 1. 後端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 填入 GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY, GROQ_API_KEY
uvicorn main:app --reload
```

### 2. 匯入題庫

```bash
# 在專案根目錄執行
python scripts/import_questions.py
```

### 3. 前端

```bash
cd frontend
pip install -r requirements.txt
reflex run
```

網址：http://localhost:3000

## 開發進度

| Phase | 目標 | 狀態 |
|-------|------|------|
| Phase 1 | 基礎建設（登入、路由、資料庫） | ✅ 完成 |
| Phase 2 | 題庫系統（匯入、CRUD） | ✅ 完成 |
| Phase 3 | 核心答題流程 | ✅ 完成 |
| Phase 4 | 成績與歷史紀錄 | ✅ 完成 |
| Phase 5 | AI 功能（hint、弱點分析） | ✅ 完成 |
| Phase 6 | 老師端 | 規劃中 |
| Phase 7 | 管理員端 | 規劃中 |

## 環境變數（backend/.env）

```
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
FRONTEND_URL=http://localhost:3000
DATABASE_URL=sqlite:///./exam.db
SECRET_KEY=...
GROQ_API_KEY=...
```

## 文件

- [`docs/Spec.md`](docs/Spec.md) — 頁面規格文件
- [`docs/Todo.md`](docs/Todo.md) — 開發任務清單
- [`docs/Future.md`](docs/Future.md) — 未來擴充規劃（老師端 / 管理員端）
- [`docs/QuestionBank.md`](docs/QuestionBank.md) — 題庫格式說明
- [`docs/AddingQuestions.md`](docs/AddingQuestions.md) — 新增考古題流程
