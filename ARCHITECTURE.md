# Trendsetter Dashboard - 系統架構 (Architecture)

## 1. 系統概觀
本專案是一個全自動化的美股多維度市場分析儀表板。它整合了情緒、廣度、期權、內部資金及宏觀數據，為使用者提供一站式的決策輔助界面。

## 2. 技術棧 (Tech Stack)
- **語言**: Python 3.9+
- **虛擬環境**: `.venv` (強制於本地開發與執行時使用)
- **數據處理與外部整合**: `gspread` (Google Sheets API), `pandas`, `yfinance`, `beautifulsoup4`, `requests`
- **前端框架**: HTML5, Vanilla CSS, Tailwind CSS (Layout), Lucide Icons (圖標), Chart.js (趨勢)
- **自動化**: GitHub Actions (**07:00 & 12:00 TPE**)
- **部署**: GitHub Pages (自動偵測主分支變更)

## 3. 核心組件與檔案結構
- `scripts/fetch_data.py`: **數據處理核心**。整合多個來源：CNN/Crypto F&G, VIX, DIX/GEX 從原 API/網頁抓取；**P/C Ratio, NAAIM, AAII 以及市場廣度 (Breadth)** 已遷移至 **私人 Google Sheet (Log 分頁)** 讀取，以確保數據準確性並跳過複雜防爬機制。
- `scripts/generate_html.py`: **多頁面生成器**。利用 Template 邏輯生成 `index.html` (儀表板)、`charts.html` (圖表區) 與 `history.html` (歷史紀錄)。
- `data/history.json`: **本地資料庫**。以 JSON 格式儲存所有歷史交易日的清洗後數據。
- `.github/workflows/daily_update.yml`: **自動化 CI/CD**。透過 GitHub Secrets (`GSHEET_CREDENTIALS`) 安全連線至試算表進行每日兩次的自動更新。
- `.agents/`: **AI 助理資源**。包含開發規範 (`instructions.md`) 與常用工作流指令 (`workflows/`)。

## 4. 數據獲取源 (Data Dimensions)
- **情緒 (Sentiment)**: **Google Sheet (NAAIM, AAII)**, CNN F&G, Crypto F&G (API)。
- **風險與期權 (Risk & Options)**: **Google Sheet (Equity/Total P/C Ratios)**, VIX, GEX (Gamma Exposure)。
- **內部資金與廣度 (Internals)**: **Google Sheet (NYSE/NASD 20MA & 50MA)**, DIX (Dark Pool Index)。*註：原 WSJ AD Issues 已停用。*
- **宏觀趨勢 (Macro)**: 10Y-3M 利差、HYG/LQD、XLY/XLP、銅金比 (Copper/Gold) 及 KBE/SPY 比值。

## 5. UI/UX 特色
- **線性橫向佈局 (Horizontal Row Flow)**: 各大分類以整列呈現，提升閱讀清晰度。
- **歷史數據過濾**: 透過 Tab 鍵快速切換宏觀、情緒、風險等不同維度的歷史表格。
- **彈性欄位對應**: 數據抓取腳本採用 Header 映射機制，確保 Google Sheet 欄位位置更動時仍能正確讀取。

## 6. 自動化與維護
- **「紀錄」指令**: AI 接收指令後會同步最新腳本邏輯至本文件，並自動 Commit & Push 至 GitHub。
- **同步策略**: 使用 **/抓取repo** 指令 (git pull --rebase)，確保本地開發腳本時不會覆蓋 GitHub Action 自動抓取的數據。
- **定時任務**: 每日台灣時間 **07:00 與 12:00** 自動執行。環境已簡化，不再依賴 Playwright 繁重安裝，執行效率提升。

---
*最後更新於: 2026/03/07*
