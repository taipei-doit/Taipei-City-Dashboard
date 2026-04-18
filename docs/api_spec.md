韌性防災 API 規格書 (v1.1)

## 1. Incident

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

## 2. Component Data

**描述：** 所有的統計圖表（長條圖、折線圖、圓餅圖）都透過統一格式回傳。

### [GET] /api/v1/component/{id}?city={city}

#### (1) 二維資料

> 對應Go結構：`TwoDimensionalDataOutput`

````json
{
  "data": [
    { "x": "板橋區", "y": 12.5 },
    { "x": "萬華區", "y": 8.3 }
  ]
}

#### (2) 時間序列
> 對應 Go 結構：`TimeSeriesDataOutput`
```json
{
  "data": [
    {
      "name": "累積降雨量",
      "data": [
        { "x": "2026-04-18T14:00:00+08:00", "y": 45.0 },
        { "x": "2026-04-18T15:00:00+08:00", "y": 52.5 }
      ]
    }
  ]
}
#### (3) 三維資料
> 對應 Go 結構：`ThreeDimensionalDataOutput`
```json
{
  "data": [
    {
      "name": "臺北市",
      "icon": "rain-icon",
      "data": [12, 15, 8] // 代表三個行政區的數值
    },
    {
      "name": "新北市",
      "icon": "rain-icon",
      "data": [20, 25, 14]
    }
  ]
}

#### (4) 地圖圖例資料
> 對應 Go 結構：`MapLegendData`
```json
{
  "name": "一級警戒區",
  "type": "flood",
  "icon": "red-drop",
  "value": 80.5
}
````
