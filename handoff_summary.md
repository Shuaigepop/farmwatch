# FarmWatch Project Handoff

## 專案位置 (Workspace)
`C:\Users\DESMOND\.gemini\antigravity\scratch\farmwatch`

## 專案狀態 (Current State)
1. **前端 (Frontend)**: 原生 HTML/JS/CSS (SPA 架構)，不使用任何框架。
   - `frontend/index.html` 包含基礎 HTML 架構與 CSS 引用。
   - `frontend/js/app.js` 為核心路由，使用 `#` hash 路由。
   - `frontend/js/components/` 包含所有的 UI 元件 (如 inventory.js, settings.js, daily-summary.js 等)。
   - **重要修正**: 為了避免 Windows 環境下字元編碼錯誤導致白屏，前端所有 import 已加上 `?v=9` 避免快取，且後端 `main.py` 已加入強制 `charset=utf-8` 的 middleware。
2. **後端 (Backend)**: Python FastAPI + SQLite (`aiosqlite`)。
   - 位於 `backend/` 資料夾，主程式為 `main.py`。
   - 已完成 Auth, Farms, Inventory, Tasks, Photos, Messages, Webhook 等 API 開發。
   - 資料庫為 `backend/farmwatch.db`。
   - 運行指令: `uvicorn main:app --host 127.0.0.1 --port 8000`
3. **基礎架構**:
   - Ngrok: 供外部與 LINE Bot Webhook 使用。
   - API 呼叫 (`apiFetch`): 已加上 `ngrok-skip-browser-warning: true` 標頭以解決 Ngrok 攔截造成的 405 Method Not Allowed 錯誤。

## 下一步目標 (Next Steps)
接下來的使用者需求為 **「AI Agent 系統整合 (Multi-Agent Integration)」**，包含：
1. **系統排程 Agent**: 每天固定時間執行並生成所有菜園的 AI Daily Insights。
2. **任務 Agent**: 自動化分配任務與排程。
請參考 `implementation_plan.md` 以進行後續的 AI Agent 開發。

## 給下一位 Agent 的指示 (Instructions for the next Agent)
- 開發時請注意檔案編碼，使用 Python 寫入檔案或使用 PowerShell `Out-File` 時，務必確保為 `UTF-8`。
- 接手後請先啟動後端伺服器 (若尚未啟動) 並確認前端畫面與 API 是否運作正常。
- 遵循使用者對外觀的極高要求 (Premium Design)，維持目前的 Glassmorphism 與流暢動畫風格。
