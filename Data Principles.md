# 資料抓取規範 (Data Principles)

為了確保儀表板的歷史資料長久正確，所有資料爬蟲與獲取程式（如 `fetch_data.py`）必須嚴格遵守以下守則：

## 1. 嚴格對時，寧缺勿濫 (No Fallback to Previous Days)
抓取指定日期 (`target_dt`) 的資料時，**如果當天沒有發布資料，請直接回傳 `None`，絕對不可以拿昨天或過去的最新資料來填補。**
*   **原因**：如果填入過去的資料，會導致歷史紀錄無法反映該天真實「無新資料」的狀態，並且會破壞前端儀表板判斷資料是否延遲的「DELAYED標籤」機制。
*   **實務作法**：不管是 API、FRED 或 yfinance，請一律使用明確的 start 與 end 範圍 (`start = target_date`, `end = target_date`) 來限制。如果回傳空值，就直接讓該欄位為空。

## 2. 自動回補機制 (Automatic Backfill)
每次執行每日更新時，系統都要檢查過去幾個工作天是否有沒長出來的最新資料。
*   **作法**：定義一個 `essential_keys` 清單（包含關鍵代表性指標），只要歷史紀錄中該天的這些關鍵指標出現空值 (`None`)，就在這次執行中一併補抓該天的資料，確保如果資料隔天或稍晚發布後能被正確補上。

## 3. 專屬日期的資料抓取函式 (Date-specific Fetching)
所有的 `fetch_xxx` 函式都必須能接受一個 `target_dt` 參數。函式內部要基於這個 `target_dt` 去向各網站請求特定一天的資料，而不只是盲目地戳 `/latest` 的 API。