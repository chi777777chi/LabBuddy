# Todo.md — 醫檢師國考線上題庫平台 開發任務清單

## 技術選型
- 後端：FastAPI
- 前端：Reflex 0.9（純 Python，底層編譯成 React，支援手機端響應式）
- AI：Groq API（llama-3.3-70b-versatile）

---

## Phase 1｜基礎建設
> 目標：專案可以跑起來、用 Google 登入

- [x] 建立專案結構（FastAPI + Reflex）
- [x] 設計資料庫 schema（User、Subject、Question、ExamSession、Answer）
- [x] 整合 Google OAuth 登入
- [x] 建立基本頁面路由（首頁、登入頁、主選單）

---

## Phase 2｜題庫系統
> 目標：題目可以存入資料庫並查詢

- [x] 定義題目資料格式（JSON）
- [x] 建立六大科目分類結構（Subject model）
- [x] 完善資料庫 schema（Question、ExamSession、Answer model）
- [x] 建立 Question / Subject CRUD API
- [x] 撰寫考古題批次匯入工具

---

## Phase 3｜核心答題流程
> 目標：學生可以完整做一份考卷

### 後端
- [x] `POST /exam/start`：建立 ExamSession，依設定抽出題目清單
  - [x] 出題邏輯：單份完整（指定年份＋梯次）
  - [x] 出題邏輯：單份隨機（從單份隨機抽 N 題）
  - [x] 出題邏輯：多份隨機（跨多份隨機抽 N 題）
  - [x] 選項隨機（A/B/C/D 順序打亂，答案對應調整）
- [x] `POST /exam/{session_id}/answer`：記錄單題作答（chosen、time_spent）
- [x] `POST /exam/{session_id}/submit`：交卷，計算分數寫入 ExamSession

### 前端
- [x] 測驗設定頁：選科目、題數（5／10／80）、出題邏輯、計時模式、即時對答、隨機選項、儲存歷史
- [x] 答題介面
  - [x] 單題呈現（題號、題目、選項）
  - [x] 題目來源標註（e.g. 114年第二次 臨床生理 第3題）
  - [x] 選項刪去法（點擊劃線，再點取消）
  - [x] 選項點選高亮
  - [x] 即時模式：作答後立即顯示正確答案（含對錯標色，1 秒後自動前進）
  - [ ] 詳解：顯示每題的 AI 解釋或來源說明
- [x] 進度條（e.g. 3 / 10）
- [x] 上一題 / 下一題 / 提早交卷按鈕
  - [x] 返回主選單確認 dialog
  - [x] 提早交卷 / 交卷確認 dialog（顯示未作答題數）
- [x] 計時器（每題 90 秒，倒數顯示，< 30 秒變紅，時間到自動交卷）

---

## Phase 4｜成績與歷史紀錄
> 目標：學生可以查看成績、翻閱紀錄

### 後端
- [x] `POST /exam/{session_id}/submit`：回傳本次成績、各題對錯、答案詳情
- [x] `GET /exam/history`：回傳歷次測驗列表
- [x] `GET /exam/{session_id}/detail`：回傳單次測驗詳細紀錄
- [x] `GET /exam/wrong-questions`：依科目統計有答錯紀錄的題目數
- [x] QuestionStats 表：追蹤每位用戶對每道題的累計答對／答錯次數

### 前端
- [x] 成績頁：答對率、各題回顧（題目＋你的答案＋正確答案＋對錯）
- [x] 模擬考模式：關閉即時對答，交卷後才在成績頁顯示對錯（詳解尚未實作）
- [x] 歷史紀錄頁：列出所有已儲存的測驗（日期、科目、年份梯次、答對率）
- [x] 單次報告詳細頁：點擊歷史紀錄卡片，dialog 顯示每題作答詳情
- [x] 錯題複習頁：依科目統計答錯次數，一鍵開始複習，答題中顯示歷史對錯次數
- [ ] 詳解功能：成績頁 / 歷史詳情顯示每題 AI 或來源解釋
- [x] PDF 匯出（每題含選項內容，顏色標示對錯，可從成績頁與歷史詳情下載）

---

## Phase 5｜AI 功能
> 目標：AI 輔助分析與智慧出題

### 後端
- [ ] 題目難易度分級（easy / medium / hard）
- [ ] 自適應出題加權邏輯（弱點題型出現頻率提升）
- [x] `GET /analytics/me`：各科答對率、成績趨勢、最常答錯題目、AI 學習建議
- [x] `POST /ai/hint`：分階段 AI 提示（Groq llama-3.3-70b）
- [x] `GET /users/me/stats`：個人學習統計（場數、答題數、答對率、最愛科目）

### 前端
- [x] 答題中 AI 分階段提示按鈕（3 層遞進，每題各自計算，設定頁開關控制）
- [x] 弱點分析頁（/analytics）：科目卡片、成績折線圖、弱點題列表、AI 建議
- [x] 個人資料頁（/profile）：學習統計、快速導航
- [ ] AI 生成模擬試卷（stretch goal）

---

## Phase 6｜老師端（未來）
> 見 docs/Future.md

## Phase 7｜管理員端（未來）
> 見 docs/Future.md
