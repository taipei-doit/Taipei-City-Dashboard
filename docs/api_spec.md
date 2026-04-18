韌性防災 API 規格書 (v1.0)

## 1. 模型：Incident

| JSON 欄位名     | 型態     | 來源     | 說明                       |
| :-------------- | :------- | :------- | :------------------------- |
| `ID`            | int64    | 原有     | 唯一識別碼 (注意大小寫)    |
| `inctype`       | string   | 原有     | 災情類型 (如: FLOOD)       |
| `description`   | string   | 原有     | 詳細敘述                   |
| `distance`      | float64  | 原有     | 距離                       |
| `latitude`      | float64  | 原有     | 緯度                       |
| `longitude`     | float64  | 原有     | 經度                       |
| `place`         | string   | 原有     | 地點名稱                   |
| `reportTime`    | datetime | 原有     | 報案時間                   |
| `status`        | string   | 原有     | 處理狀態                   |
| **`city`**      | string   | **新增** | 縣市 (TP/NTP)              |
| **`aiSummary`** | string   | **新增** | AI 生成摘要                |
| **`aiRisk`**    | string   | **新增** | AI 評估等級 (High/Med/Low) |

```json
{
  "ID": 1,
  "inctype": "FLOOD",
  "description": "大漢溪水位上升",
  "distance": 0,
  "latitude": 25.012,
  "longitude": 121.465,
  "place": "新北市板橋區...",
  "reportTime": "2026-04-18T14:00:00Z",
  "status": "open",
  "city": "NTP",
  "aiSummary": "水位即將達警戒線，請撤離低窪地區。",
  "aiRisk": "High"
}
```
