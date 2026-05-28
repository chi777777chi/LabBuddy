# Todo.md — 醫檢師國考線上題庫平台 開發任務清單

## 技術選型
- 後端：FastAPI
- 前端：Reflex 0.9（純 Python，底層編譯成 React，支援手機端響應式）
- AI（使用者端功能）：Google Gemini API（`google-generativeai` 套件，目前模型 `gemini-2.0-flash-lite`）
  - 包含：AI 提示、AI 解析、學習分析 AI 建議
- AI（開發者腳本）：Groq API（llama-3.3-70b-versatile）
  - 包含：classify_difficulty.py、classify_tags.py 等批次處理腳本

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
- [x] 題目難易度分級（easy / medium / hard）— `Question.difficulty` 欄位已建，`scripts/classify_difficulty.py` 批次分類中（進行中，每日額度重置後繼續跑）
- [x] 自適應出題加權邏輯（弱點題型出現頻率提升）— `adaptive` 出題模式，加權不重複抽樣
- [x] `GET /analytics/me`：各科答對率、成績趨勢、最常答錯題目、AI 學習建議
  - AI 建議結果持久化存入 DB（`users.ai_analysis_text` + `users.ai_analysis_answer_count`）
  - 答題數不變時直接回傳 DB 快取，不重打 Gemini API，避免每次進首頁就耗配額
- [x] `POST /ai/hint`：分階段 AI 提示（Gemini）
- [x] `POST /ai/explain`：個人化 AI 解析（Gemini），結合四個弱點維度
- [x] `GET /users/me/stats`：個人學習統計（場數、答題數、答對率、最愛科目）

### 前端
- [x] 答題中 AI 分階段提示按鈕（3 層遞進，每題各自計算，設定頁開關控制）
- [x] 難度篩選選項（全部／簡單／中等／困難）
- [x] 自適應模式選項（設定頁）
- [x] 弱點分析頁（/analytics）：科目卡片、成績折線圖、弱點題列表、AI 建議
- [x] 個人資料頁（/profile）：學習統計、快速導航
- [x] 成績頁 / 歷史詳情每題加「AI 解析」按鈕（dialog 顯示，loading 狀態＋錯誤處理）
- [ ] AI 生成模擬試卷（stretch goal）

---

## Phase 6｜老師端
> 目標：老師可建立班級、邀請學生、查看全班與個人進度

### 6-A. DB 擴充
- [x] 新增 `Class` 表：id, name, teacher_id (FK→users), invite_code (6碼英數), created_at
- [x] 新增 `ClassMember` 表：id, class_id (FK→classes), student_id (FK→users), joined_at
- [x] `backend/main.py` 加自動 migration（同 `is_active` 的 ALTER TABLE 做法）

### 6-B. 後端 API（新增 `backend/api/routes/teacher.py`）
- [x] `require_teacher` dependency（role=teacher 或 admin，否則 403）
- [x] `POST /teacher/classes` — 建立班級（自動產生隨機 6 碼邀請碼）
- [x] `GET /teacher/classes` — 取得老師所有班級列表
- [x] `GET /teacher/classes/{class_id}` — 班級詳情＋學生名單（含最近作答日、場次、平均分）
- [x] `POST /teacher/classes/{class_id}/regenerate-code` — 重新產生邀請碼
- [x] `GET /teacher/classes/{class_id}/students/{student_id}` — 學生個人進度（歷史紀錄＋各科答對率）
- [x] `GET /teacher/classes/{class_id}/stats` — 全班統計（各科平均答對率、Top 10 錯誤題）
- [x] `POST /classes/join` — 學生輸入邀請碼加入班級（學生端呼叫，不需 teacher 角色）
- [x] `backend/main.py` 註冊 teacher router

### 6-C. 前端 State（新增 `frontend/app/state/teacher_state.py`）
- [x] 班級列表、當前班級詳情、學生名單、全班統計資料等欄位
- [x] `load_classes` / `create_class` / `regenerate_code`
- [x] `load_class_detail` / `load_student_progress` / `load_class_stats`

### 6-D. 前端頁面
- [x] `/teacher` — 老師主選單（班級列表卡片、建立新班級按鈕）
- [x] `/teacher/class/[class_id]` — 班級管理頁（學生名單、邀請碼顯示／複製／重新產生）
- [x] `/teacher/student/[student_id]` — 學生個人進度頁（各科答對率卡片＋測驗歷史）
- [x] `/teacher/stats/[class_id]` — 全班統計頁（各科平均答對率、全班最常答錯 Top 10）
- [x] 學生端主選單加「加入班級」入口（輸入邀請碼 dialog）
- [x] 登入後依 role 自動導向：student→/home、teacher→/teacher、admin→/admin
- [x] `frontend/app/app.py` 註冊新頁面

## Phase 7｜管理員端
> 目標：管理員可管理使用者與題庫

### 後端
- [x] `GET /admin/users`：所有使用者列表
- [x] `PATCH /admin/users/{id}/role`：指派角色（student／teacher／admin）
- [x] `PATCH /admin/users/{id}/ban`：停權／恢復
- [x] `GET /admin/stats`：全平台數據（使用者數、答題數、題庫量、各科題數）
- [x] `GET /admin/questions`：題庫列表（科目／年份篩選＋分頁）
- [x] `POST /admin/questions`：新增題目
- [x] `PATCH /admin/questions/{id}`：編輯題目
- [x] `DELETE /admin/questions/{id}`：刪除題目

### 前端
- [x] `/admin`：平台總覽（7 張統計卡＋各科題數）
- [x] `/admin/users`：使用者管理（角色指派＋停權按鈕）
- [x] `/admin/questions`：題庫維護（篩選／分頁／跳頁／新增編輯刪除）

---

## Phase 8｜Bug 修復與功能補完（2026-05-28）

### Bug 1：Safari Google 登入 403
- [ ] 用 Safari DevTools → Network tab 確認 403 來自 Google 端還是 `/api/auth/callback`
- [ ] 確認 Google Console 的 Authorized redirect URIs 格式是否相容 Safari
- [ ] 查 nginx 有無缺少 CORS header
- [ ] 測試是否為 SameSite cookie 問題（Safari 對第三方 cookie 限制較嚴）

### Bug 2：學習分析頁面跳轉失敗
- 症狀：點學習分析按鈕後跳回主頁，無法停在 `/analytics`
- 根本原因：`load_analytics` 有 race condition，token 未就緒時觸發 `rx.redirect("/")`
- 已修正：改為靜默 return，並在 home page on_load 預先觸發 analytics 載入
- **Debug 步驟（若問題仍存在）：**
  - [ ] 點按鈕後觀察 URL 有無閃到 `/analytics`（有閃 = 頁面進去但被踢走；沒閃 = 按鈕問題）
  - [ ] 直接在網址列輸入 `/analytics` 測試能否停留
  - [ ] server 執行 `sudo journalctl -u medexam-api -f` 同時點按鈕，確認是否有 `/analytics/me` 請求抵達
  - [ ] `curl "http://127.0.0.1:8000/analytics/me?token=<token>"` 確認 API 正常回傳
  - [ ] 瀏覽器 F12 → Console 看有無 JS 錯誤

### Bug 3：PDF 匯出壞掉 ✅ 已修復
- 症狀：手機 `ERR_CONNECTION_REFUSED`；電腦跳至 `http://localhost:8000/...`
- 根本原因 1：export URL 使用 `BACKEND_URL`（`localhost:8000`），瀏覽器無法連到 server 內部位址
- 根本原因 2：server 缺少支援 TrueType outlines 的 CJK 字型，導致中文顯示為方塊
- [x] `auth_state.py` 新增 `BACKEND_PUBLIC_URL`（從環境變數讀取，server 由 systemd 注入 `http://151.145.71.45/api`）
- [x] `exam_state.py` / `history_state.py` PDF redirect 改用 `BACKEND_PUBLIC_URL`
- [x] server 安裝 `fonts-wqy-microhei`（TrueType outlines，reportlab 相容）
- [x] `backend/utils/pdf.py` 更新字型偵測路徑，加入 WQY 字型；`.ttc` 檔案改用 `subfontIndex=0` 載入
- 注意：Noto CJK（`fonts-noto-cjk`）使用 PostScript outlines（CFF），reportlab 不支援，不可用

### Bug 4：classify_tags.py 解析失敗
- 症狀：每批 15 題全部 `ParseFail`，ok=0 fail=15
- 原因：AI 回傳格式與解析 regex 不符
- [ ] 加 debug 輸出，印出 AI 實際回傳的原始文字
- [ ] 縮小批次為 1 題，確認單題是否可解析
- [ ] 調整 prompt，明確要求回傳固定 JSON 格式
- [ ] 更新解析邏輯
- [ ] 全量跑完後確認 DB 的 `questions.tags` 已填入

### Feature：AI 解析（答題後個人化解釋）✅ 已完成（待配額重置驗證）
- 目標：答完一題後，AI 結合多維弱點依據提供個人化解析
- **四個弱點分析維度（已確認採用）：**
  1. **難度失分分布**：easy/medium/hard 各難度答對率，判斷基礎或進階哪裡弱
  2. **作答時間**：花時間長但答錯 = 強烈弱點；花時間長但答對 = 不夠熟練
  3. **錯誤選項模式**：使用者重複選同一個錯誤選項，代表有特定錯誤觀念
  4. **科目層級正確率**：宏觀弱點科目
  - （bonus）**知識點標籤**：classify_tags 完成後可加入，更精準指出弱點單元
- 優點：前四項立即可用，不需等 classify_tags 跑完
- [x] 後端：彙整弱點資料的 helper function
  - 撈 Answer 計算各難度答對率
  - 撈 Answer 計算平均作答時間（與 75秒/題 標準比較）
  - 撈 Answer 統計重複錯誤選項（`chosen` 出現最多次的非正解）
  - 撈 QuestionStats 算各科正確率
- [x] 後端：新增 `POST /ai/explain` endpoint
  - 輸入：question_id, chosen, token
  - 組合弱點摘要 + 題目內容 + 正確答案 + 使用者選擇 → prompt
  - 呼叫 Gemini API 回傳三段式解析（解題解析 / 常見錯誤分析 / 學習建議）
- [x] 前端：成績頁 / 歷史詳情每題加「AI 解析」按鈕（點擊呼叫 API，顯示 loading → 解析文字）
- [x] 前端 try/except 修正：timeout 後正確顯示錯誤訊息，不再卡在轉圈
- [ ] 前端：即時對答答完後也可選擇看 AI 解析
- [ ] 知識點標籤維度：等 classify_tags 跑完後加入 prompt
- [ ] 考慮 cache：同一 question_id + 使用者的解析可暫存，避免重複呼叫

### Bug 5：HTTPS 升級後登入與 WebSocket 全面失效 ✅ 已修復（2026-05-28）
- 症狀：
  1. Google 登入後跳到 `http://labbuddy.duckdns.org/callback/?jwt=...`，nginx 回 404
  2. 登入成功後 WebSocket 連線失敗：`Cannot connect to server at ws://151.145.71.45/_event`
- 根本原因：
  1. `backend/.env` 的 `GOOGLE_REDIRECT_URI` 和 `FRONTEND_URL` 仍指向 `duckdns.org`（HTTP），但 SSL cert 只有 `dpdns.org`
  2. 前端登入按鈕用 `rx.link`，React Router 把同源 URL 當 client-side route 處理，導致 Reflex 回 404
  3. `REFLEX_API_URL` 未設定，Reflex 編譯時嵌入 server IP（`151.145.71.45`），瀏覽器用 `ws://`（非加密）連線
- 修復：
  - [x] `backend/.env`：`GOOGLE_REDIRECT_URI` 和 `FRONTEND_URL` 統一改為 `https://labbuddy.dpdns.org`
  - [x] `frontend/app/pages/login.py`：登入按鈕改用 `rx.call_script("window.location.href=...")`，繞過 React Router
  - [x] 前端重啟時帶入 `REFLEX_API_URL=https://labbuddy.dpdns.org`，WebSocket 改走 `wss://`（加密）
  - [x] Google OAuth Console 新增 `https://labbuddy.dpdns.org/api/auth/callback`
- 注意：統一使用 `https://labbuddy.dpdns.org`，`duckdns.org` 僅作 nginx alias，但不用於 OAuth

**已知問題與 Background（2026-05-28）：**
- Gemini free tier 每日配額（RPD）容易被耗盡：
  - 根本原因：`/analytics/me` 每次載入都打一次 AI，而 home page 有預先載入 analytics
  - 已修：analytics AI 建議改存 DB，答題數不變就不重打（`users.ai_analysis_text` + `users.ai_analysis_answer_count`）
- Gemini 模型命名問題（`google-generativeai` v1beta）：
  - `gemini-1.5-flash` / `gemini-1.5-flash-latest` → 404 不支援
  - `gemini-2.0-flash` → 可用，但今日測試已耗盡 RPD
  - `gemini-2.0-flash-lite` → 目前使用中，配額獨立
  - 明日（UTC 00:00 / 台灣時間 08:00）配額重置後可正常測試
- Gemini 內部 auto-retry 在配額耗盡時會靜默重試數分鐘才報錯 → 已加 `retry=None` 停用
