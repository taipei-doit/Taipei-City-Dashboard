# Component AI Summary — Airflow Trigger API

## 用途
指定單一組件的 `index`（+選填 `city`/`type`），只重新生成該組件的 AI 摘要，不影響其他組件、不受 `enable_ai_summary` 開關限制。

---

## 觸發 API

**`POST /api/v1/dags/proj_city_dashboard_component_ai_summary/dagRuns`**

完整 URL（SIT）：
```
https://test-citydashboard.taipei/airflow-sit/api/v1/dags/proj_city_dashboard_component_ai_summary/dagRuns
```

**認證**：HTTP Basic Auth，用專屬的服務帳號（範圍只限這支 DAG，見文末說明）
```
Username: component_ai_summary_svc
Password: <向資料工程team索取,不寫在這份文件裡>
```

**Headers**
```
Content-Type: application/json
```

**Request Body**

| 欄位 | 型別 | 必填 | 說明 |
|---|---|---|---|
| `conf.index` | string | ✅ | 組件 index。**不帶這個欄位會退回正常批次模式，掃全部 `enable_ai_summary=true` 的組件**，不是單一組件模式，務必要帶 |
| `conf.city` | string | 選填 | 不帶就該 `index` 底下所有 city 都重新生成 |
| `conf.type` | string | 選填 | `"chart"` 或 `"map"`。不帶就 chart+map 都重新生成。帶其他值會讓這次執行失敗（見下方錯誤處理） |

**Request 範例**
```bash
curl -X POST \
  -u "component_ai_summary_svc:<password>" \
  -H "Content-Type: application/json" \
  -d '{"conf": {"index": "aging_kpi", "city": "taipei", "type": "chart"}}' \
  "https://test-citydashboard.taipei/airflow-sit/api/v1/dags/proj_city_dashboard_component_ai_summary/dagRuns"
```

**Response（HTTP 200，立即回，非同步）**
```json
{
  "conf": {"city": "taipei", "index": "aging_kpi", "type": "chart"},
  "dag_id": "proj_city_dashboard_component_ai_summary",
  "dag_run_id": "manual__2026-07-14T06:10:01.165951+00:00",
  "state": "queued",
  "execution_date": "2026-07-14T06:10:01.165951+00:00",
  "start_date": null,
  "end_date": null
}
```

⚠️ **這支 API 是非同步的**：回應只代表「已排入佇列」，`state: queued`，不代表摘要已經生成完畢。實際執行約 15～30 秒（要真的呼叫 LLM + 查詢資料庫）。要拿到結果，有兩種方式：

---

## 查詢執行狀態（選用）

**`GET /api/v1/dags/proj_city_dashboard_component_ai_summary/dagRuns/{dag_run_id}`**

用觸發回應裡的 `dag_run_id`（原樣帶入即可，不要自己組）：

```bash
curl -u "component_ai_summary_svc:<password>" \
  "https://test-citydashboard.taipei/airflow-sit/api/v1/dags/proj_city_dashboard_component_ai_summary/dagRuns/manual__2026-07-14T06%3A10%3A01.165951%2B00%3A00"
```

> `dag_run_id` 裡的 `:`、`+` 要做 URL encode（`%3A`、`%2B`），大部分 HTTP client library 會自動處理，手動組 URL 時要注意。

`state` 欄位：`queued` → `running` → `success` 或 `failed`。

**建議做法**：如果只是想確認「摘要有沒有更新」，直接查 `component_ai_summary` 表的 `updated_at` 通常比輪詢 Airflow API 簡單（見下方）。

---

## 摘要結果存放位置

生成結果寫入 `component_ai_summary` 表（dashboard DB）：

| 欄位 | 說明 |
|---|---|
| `index` / `city` / `type` | 對應觸發時帶的參數（`type` 固定是 `chart` 或 `map`，不會是別的值） |
| `result` | AI 生成的摘要內文 |
| `updated_at` | 寫入時間，可用來判斷是否為這次觸發產生的新結果 |

同一個 `(index, city, type)` 每次生成都是**新增一筆**（append-only），不是更新既有列，所以要拿「最新」摘要要 `ORDER BY updated_at DESC LIMIT 1`。

### 圖層合併說明
一個組件如果有多個地圖圖層（`map_config_ids` 有多筆），**不會**每個圖層各打一次 AI、各寫一筆——是把所有圖層的資訊（欄位說明、顏色對照、查詢樣本）合併成一份 prompt，只呼叫一次 AI，`type='map'` 永遠只寫 **1 筆**，內容是綜合所有圖層寫成的一段摘要。

---

## 錯誤處理

- `conf.type` 帶了 `"chart"`/`"map"` 以外的值：**觸發本身仍會回 200/queued**，但實際執行時該次 DagRun 會 `state: failed`（輸入驗證在 DAG 內部做，不是在觸發當下擋）。如果要確保參數正確，請自行在送出前驗證 `type` 只能是這兩個值之一。
- `conf.index` 查無對應組件（打錯字或不存在）：DagRun 會正常跑完 `state: success`，但不會寫入任何摘要（DAG 內部會印 log 說明查無此組件，但不會讓整個 run 失敗）。

---

## 帳號權限範圍

`component_ai_summary_svc` 是專門為這支 API 建立的服務帳號，權限已收斂到只能對 `proj_city_dashboard_component_ai_summary` 這支 DAG 做 GET（查狀態）/POST（觸發），對其他任何 DAG 都會是 `403 Forbidden`，也**沒有** Connections/Variables/Users 等管理權限——即使外洩，影響範圍就只有「有人可以亂觸發這支摘要 DAG」，不會動到密碼、DB 連線字串等敏感設定。

密碼請跟資料工程 team 索取，不會寫在這份文件或 git 歷史裡。
