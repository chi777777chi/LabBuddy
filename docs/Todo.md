# Todo.md — 醫檢師國考線上題庫平台 開發任務清單

## 技術選型
- 後端：FastAPI
- 前端：Reflex（純 Python，底層編譯成 React，支援手機端響應式）
- AI：Claude API

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
- [ ] 測驗設定頁：選科目、題數（5／10／80）、出題邏輯、計時模式、詳解模式
- [ ] 答題介面
  - [ ] 單題呈現（題號、題目、選項）
  - [ ] 題目來源標註（e.g. 114年第二次 臨床生理 第3題）
  - [ ] 選項刪去法（點擊劃線，再點取消）
  - [ ] 選項點選高亮
  - [ ] 即時模式：作答後立即顯示正確答案
- [ ] 進度條（e.g. 3 / 10）
- [ ] 上一題 / 下一題 / 提早交卷按鈕
- [ ] 計時器（單題用時 ＋ 剩餘總時間，可關閉）

---

## Phase 4｜成績與歷史紀錄
> 目標：學生可以查看成績、翻閱紀錄

### 後端
- [ ] `GET /exam/{session_id}/result`：回傳本次成績、各題對錯、答案詳情
- [ ] `GET /users/me/history`：回傳歷次測驗列表
- [ ] `GET /users/me/history/{session_id}`：回傳單次測驗詳細紀錄

### 前端
- [ ] 成績頁：答對率、花費時間、各題回顧（題目＋你的答案＋正確答案＋對錯）
- [ ] 模擬考模式：交卷後才在成績頁顯示詳解
- [ ] 歷史紀錄頁：列出所有已儲存的測驗（日期、科目、答對率）
- [ ] 單次報告詳細頁（點進歷史紀錄查看）
- [ ] PDF 匯出（試卷 + 作答紀錄）

---

## Phase 5｜AI 功能
> 目標：AI 輔助分析與智慧出題

### 後端
- [ ] 呼叫 Claude API 做題目難易度分級（easy / medium / hard）
- [ ] `GET /users/me/weakness`：根據歷史答題分析弱點知識點
- [ ] 自適應出題加權邏輯（弱點題型出現頻率提升）
- [ ] 成長追蹤報告（比較歷次成績趨勢）

### 前端
- [ ] 答題中 AI 提示按鈕（呼叫後顯示提示，不洩漏答案）
- [ ] 弱點分析報告頁
- [ ] 成長追蹤圖表（各科答對率趨勢）
- [ ] AI 生成模擬試卷（stretch goal）
