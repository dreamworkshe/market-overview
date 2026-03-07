# Market Overview Dashboard - 系統架構 (Architecture)

## 1. 系統概觀
本專案是一個全自動化的美股多維度市場分析儀表板。它整合了情緒、廣度、期權、內部資金及宏觀數據，為使用者提供一站式的決策輔助界面。

## 2. 技術棧 (Tech Stack)
- **語言**: Python 3.9+
- **虛擬環境**: `.venv` (強制於本地開發與執行時使用)
- **數據爬取與處理**: `Playwright` (Chromium 引擎), `pandas`, `yfinance`, `beautifulsoup4`, `requests`
- **前端框架**: HTML5, Vanilla CSS, Tailwind CSS (Layout), Lucide Icons (圖標), Chart.js (趨勢)
- **自動化**: GitHub Actions (23:00 UTC / 07:00 TPE)
- **部署**: GitHub Pages (自動偵測主分支變更)

## 3. 核心組件與檔案結構
- `scripts/fetch_data.py`: **數據處理核心**。使用 Playwright 模擬真實瀏覽器，穩定抓取 CNN/Crypto F&G, VIX, P/C Ratio, DIX/GEX, NAAIM/AAII 等指標。目前已遷移至 WSJ (AD Issues) 與 Barchart (Momentum) 以解決擋爬問題。
- `scripts/generate_html.py`: **多頁面生成器**。利用 Template 邏輯生成 `index.html` (儀表板)、`charts.html` (圖表區) 與 `history.html` (歷史紀錄)。
- `data/history.json`: **本地資料庫**。以 JSON 格式儲存所有歷史交易日的清洗後數據。
- `.github/workflows/daily_update.yml`: **自動化 CI/CD**。環境已整合 Playwright 與相關瀏覽器核心，定時執行數據更新。
- `.agents/`: **AI 助理資源**。包含開發規範 (`instructions.md`) 與常用工作流指令 (`workflows/`)。

## 4. 數據獲取源 (Data Dimensions)
- **情緒 (Sentiment)**: CNN F&G, Crypto F&G, NAAIM, AAII (從 Investing.com 等穩定源同步)。
- **風險與期權 (Risk & Options)**: CBOE/WSJ Equity/Total P/C Ratios, VIX, GEX (Gamma Exposure)。
- **內部資金與廣度 (Internals)**: **WSJ Markets Diary (NYSE/NASD AD Issues)**、DIX (Dark Pool Index)、NYSE/NASD 20MA & 50MA 廣度 (Barchart)。
- **宏觀趨勢 (Macro)**: 10Y-3M 利差、HYG/LQD、XLY/XLP、銅金比 (Copper/Gold) 及 KBE/SPY 比值。

## 5. UI/UX 特色
- **AD Ratio 視覺化**: 新增上漲/下跌家數比例 (AD Ratio)，提供比 MA 比例更具即時性的市場深度觀察。
- **三頁導頁**: 獨立的「儀表板 (Dashboard)」、「圖表區 (Charts)」與「歷史紀錄 (History)」，動態橫向導覽。
- **線性橫向佈局 (Horizontal Row Flow)**: 各大分類以整列呈現，提升閱讀清晰度。
- **歷史數據過濾**: 透過 Tab 鍵快速切換宏觀、情緒、風險等不同維度的歷史表格。

## 6. 自動化與維護
- **「紀錄」指令**: AI 接收指令後會同步最新腳本邏輯至本文件，並自動 Commit & Push 至 GitHub。
- **同步策略**: 使用 **/抓取repo** 指令 (git pull --rebase)，確保本地開發腳本時不會覆蓋 GitHub Action 自動抓取的數據。
- **定時任務**: 每日台灣時間 07:00 自動執行，環境具備自動化安裝 Playwright 瀏覽器之能力。

---
*最後更新於: 2026/03/07*
