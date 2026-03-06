# Market Overview Dashboard - 系統架構 (Architecture)

## 1. 系統概觀
本專案是一個全自動化的美股多維度市場分析儀表板。它整合了情緒、廣度、期權、內部資金及宏觀數據，為使用者提供一站式的決策輔助界面。

## 2. 技術棧 (Tech Stack)
- **語言**: Python 3.9+
- **虛擬環境**: `.venv` (隱藏目錄)
- **數據處理**: `pandas`, `yfinance`, `beautifulsoup4`, `requests`
- **前端框架**: HTML5, Vanilla CSS, Tailwind CSS (Layout), Lucide Icons (圖標), Chart.js (趨勢)
- **自動化**: GitHub Actions (23:00 UTC / 07:00 TPE)
- **部署**: GitHub Pages (自動偵測主分支變更)

## 3. 核心組件與檔案結構
- `scripts/fetch_data.py`: **數據處理核心**。抓取情緒、廣度、期權等核心指標（包含 CNN/Crypto F&G, VIX, P/C Ratio, DIX/GEX, NAAIM/AAII）。
- `scripts/generate_html.py`: **多頁面生成器**。利用 Jinja2 風格模板生成 `index.html` (儀表板)、`charts.html` (圖表區) 與 `history.html` (歷史紀錄)。
- `data/history.json`: **本地資料庫**。以 JSON 格式儲存所有歷史交易日的清洗後數據。
- `.github/workflows/daily_update.yml`: **自動化 CI/CD**。定時執行抓取與網頁發布流程。

## 4. 數據獲取源 (Data Dimensions)
- **情緒 (Sentiment)**: CNN F&G, Crypto F&G, NAAIM, AAII。
- **風險與期權 (Risk & Options)**: CBOE Equity/Total P/C Ratios, VIX, GEX (Gamma Exposure)。
- **內部資金與廣度 (Internals)**: DIX (Dark Pool Index), NYSE/NASD 20MA & 50MA 廣度（已精簡至核心 5 項指標）。
- **宏觀趨勢 (Macro)**: 10Y-3M 利差、HYG/LQD、XLY/XLP、銅金比 (Copper/Gold) 及 KBE/SPY 比值。

## 5. UI/UX 特色
- **三頁導頁**: 獨立的「儀表板 (Dashboard)」、「圖表區 (Charts)」與「歷史紀錄 (History)」，動態橫向導覽。
- **線性橫向佈局 (Horizontal Row Flow)**: 各大分類以整列呈現，提升閱讀清晰度並破除方塊網格的侷限感。
- **現代簡約美學**: 採用高品質 Light Theme、專業字體 (Plus Jakarta Sans) 與具動態悬停效果的圓角卡片。
- **響應式設計**: 在行動端自動調整為雙欄或單欄網格，確保跨裝置瀏覽品質。

## 6. 自動化與維護
- **「紀錄」指令**: AI 接收指令後會同步最新腳本邏輯至本文件，並自動 Commit & Push 至 GitHub。
- **數據管理策略**: 系統採「紐約交易日期 (US Market Date)」為基準，自動校準時區差異。
- **定時任務**: 每日台灣時間 07:00 自動執行，抓取前一晚美股收盤後的最終數據。

---
*最後更新於: 2026/03/06*
