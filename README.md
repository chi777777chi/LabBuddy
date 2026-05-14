# 醫檢師國考線上題庫平台

台灣醫事檢驗師國家考試的線上練習平台，支援六大科目考古題練習、AI 分析回饋與多角色權限管理。

## 功能特色

### 學生端
- Google OAuth 登入
- 六大科目考古題練習（可選 5 / 10 / 80 題）
- 多種出題模式：單份完整、單份隨機、多份隨機、選項隨機
- 計時模式（單題用時 + 剩餘總時間）
- 刪去法輔助答題
- 即時模式 / 模擬考模式切換
- 成績分析、歷史紀錄、PDF 匯出
- AI 弱點偵測、自適應出題、成長追蹤

### 老師端（Phase 6）
- 班級管理（邀請碼 / 邀請連結）
- 學生進度監控與全班統計

### 管理員端（Phase 7）
- 使用者權限管理
- 題庫維護
- 全平台數據總覽

## 考試科目

| # | 科目 |
|---|------|
| 1 | 臨床生理學與病理學 |
| 2 | 臨床血液學與血庫學 |
| 3 | 醫學分子檢驗學與臨床鏡檢學 |
| 4 | 微生物學與臨床微生物學 |
| 5 | 生物化學與臨床生化學 |
| 6 | 臨床血清免疫學與臨床病毒學 |

> 每年兩次考試，每年共 12 份考古題。

## 技術架構

| 層級 | 技術 |
|------|------|
| 後端 | FastAPI (Python) |
| 前端 | Reflex（純 Python，編譯為 React，支援響應式） |
| AI | Claude API (Anthropic) |
| 認證 | Google OAuth 2.0 |
| 資料庫 | PostgreSQL（或 SQLite 開發用） |

## 專案結構

```
├── backend/            # FastAPI 後端
│   ├── api/            # API 路由
│   ├── core/           # 設定、安全性
│   ├── db/             # 資料庫模型與連線
│   └── services/       # 業務邏輯（AI、出題等）
├── frontend/           # Reflex 前端
│   └── app/
│       ├── pages/      # 各頁面元件
│       ├── state/      # 全域狀態
│       └── components/ # 共用 UI 元件
├── scripts/            # 考古題批次匯入工具
└── docs/               # 專案規格文件
```

## 快速開始

### 環境需求
- Python 3.11+
- Node.js 18+（Reflex 編譯用）

### 後端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # 填入 Google OAuth、Claude API 金鑰
uvicorn main:app --reload
```

### 前端

```bash
cd frontend
pip install -r requirements.txt
reflex run
```

## 開發進度

| Phase | 目標 | 狀態 |
|-------|------|------|
| Phase 1 | 基礎建設（登入、路由、資料庫） | 規劃中 |
| Phase 2 | 題庫系統（匯入、CRUD） | 規劃中 |
| Phase 3 | 核心答題流程 | 規劃中 |
| Phase 4 | 成績與歷史紀錄 | 規劃中 |
| Phase 5 | AI 功能 | 規劃中 |
| Phase 6 | 老師端 | 未來 |
| Phase 7 | 管理員端 | 未來 |

## 文件

- [`docs/Spec.md`](docs/Spec.md) — 頁面規格文件
- [`docs/Notes.md`](docs/Notes.md) — 原始需求筆記
- [`docs/Todo.md`](docs/Todo.md) — 開發任務清單
- [`docs/Future.md`](docs/Future.md) — 未來擴充規劃
