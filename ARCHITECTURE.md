# Market Overview Dashboard - 系統架構 (Architecture)

## 1. 系統概觀
本專案是一個自動化的美股市場情緒與廣度監控儀表板。它會定期從多個免費數據源抓取數據，並生成一個直觀的網頁界面。

## 2. 技術棧 (Tech Stack)
- **語言**: Python 3.9+
- **虛擬環境**: `.venv` (隱藏目錄)
- **數據處理**: `pandas`, `yfinance`, `beautifulsoup4`, `requests`
- **前端展示**: HTML5, Tailwind CSS, Chart.js, Lucide Icons
- **自動化**: GitHub Actions (定時觸發)
- **部署**: GitHub Pages

## 3. 核心組件與檔案結構
- `scripts/fetch_data.py`: **數據處理核心**。負責抓取 CNN F&G, VIX, CBOE P/C Ratios, NAAIM, AAII 與市場廣度數據。
- `scripts/generate_html.py`: **網頁生成器**。讀取歷史數據並利用 Jinja2 模板風格生成高品質的 `index.html`。
- `data/history.json`: **資料庫**。儲存所有抓取到的歷史數據紀錄。
- `.github/workflows/daily_update.yml`: **自動化排程**。台灣時間每天 07:00 自動執行更新任務。
- `update.sh`: **本地更新腳本**。供使用者在本地手動更新與測試。

## 4. 數據獲取邏輯 (Data Sources)
- **CNN Fear & Greed**: 官方 Dataviz API。
- **VIX**: Yahoo Finance API.
- **P/C Ratios**: CBOE Daily Statistics CSV.
- **NAAIM/AAII**: 官網文字解析 (Scraping)。
- **Market Breadth**: StockCharts 標誌性符號 ($NYA50R 等)。

## 5. 自動更新流程
1. GitHub Action 觸發 (07:00 TPE)。
2. 安裝 `requirements.txt` 依賴。
3. 執行 `fetch_data.py` 將新數據寫入 `history.json`。
4. 執行 `generate_html.py` 刷新儀表板網頁。
5. 自動將變更 Commit 並 Push 回 GitHub 儲存庫。
6. GitHub Pages 自動偵測變更並部署新版網頁。

## 6. 系統維護流程 (Maintenance)
- **「紀錄」指令**: 當 AI 接收到「紀錄」指令時，會自動掃描目前的專案檔案結構、更新本 `ARCHITECTURE.md` 內容，並將變更 Commit & Push 到 GitHub。
- **數據管理策略**: 系統採「完整列優先」原則。為了圖表數據的平衡與參考價值，僅保留含有 11 個核心指標的完整紀錄。
