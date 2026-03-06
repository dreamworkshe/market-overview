# Market Overview Dashboard - 系統架構 (Architecture)

## 1. 系統概觀
本專案是一個全自動化的美股多維度市場分析儀表板。它整合了情緒、廣度、期權、內部資金及宏觀數據，為使用者提供一站式的決策輔助界面。

## 2. 技術棧 (Tech Stack)
- **語言**: Python 3.9+
- **虛擬環境**: `.venv` (隱藏目錄)
- **數據處理**: `pandas`, `yfinance`, `beautifulsoup4`, `requests`
- **前端框架**: HTML5, Tailwind CSS, Chart.js (視覺化趨勢), Lucide Icons (圖標)
- **自動化**: GitHub Actions (23:00 UTC / 07:00 TPE)
- **部署**: GitHub Pages (自動偵測主分支變更)

## 3. 核心組件與檔案結構
- `scripts/fetch_data.py`: **數據處理核心**。抓取超過 15 項核心指標，包含 CNN/Crypto F&G, VIX, P/C Ratio, DIX/GEX, McClellan Osc, NAAIM/AAII 及市場廣度數據。
- `scripts/generate_html.py`: **雙頁面生成器**。利用 Jinja2 風格模板生成 `index.html` (儀表板) 與 `history.html` (歷史紀錄)。
- `data/history.json`: **本地資料庫**。以 JSON 格式儲存所有歷史交易日的清洗後數據。
- `.github/workflows/daily_update.yml`: **自動化 CI/CD**。定時執行抓取與靜態網頁發布流程。
- `update.sh`: **本地開發腳本**。自動處理虛擬環境、依賴安裝與生成預覽。

## 4. 數據獲取源 (Data Dimensions)
- **情緒 (Sentiment)**: CNN F&G, Crypto F&G (Alternative.me), NAAIM, AAII。
- **風險與期權 (Risk & Options)**: CBOE P/C Ratios (Daily CSV), VIX (Yahoo Finance), GEX (Gamma Exposure)。
- **內部資金與廣度 (Internals)**: DIX (Dark Pool Index), McClellan Oscillator, NYSE/NASD 20MA & 50MA 廣度。
- **宏觀趨勢 (Macro)**: 10Y-3M 利差 (殖利率曲線), 金銀比 (Gold/Silver Ratio)。

## 5. UI/UX 特色
- **雙頁導航**: 獨立的視覺化首頁與數據細節頁，支援鍵盤方向鍵 (LEFT/RIGHT) 快速切換。
- **數據分類**: 首頁分為情緒、風險、內部資金與宏觀四大區塊，配備質感圖標。
- **駭客美學**: 採用 ASCII Art (Market Overview) 漸層標題與玻璃擬態 (Glassmorphism) 卡片設計。
- **防呆機制**: 動態檢測數據完整性，確保前端圖表不顯示缺失值。

## 6. 自動化與維護
- **「紀錄」指令**: AI 接收指令後會同步最新腳本邏輯至本文件，並自動 Commit & Push 至 GitHub。
- **數據管理策略**: 系統採「紐約交易日期 (US Market Date)」為基準，自動校準時區差異。
- **定時任務**: 每日台灣時間 07:00 自動執行，抓取前一晚美股收盤後的最終數據。

---
*最後更新於: 2026/03/06*
