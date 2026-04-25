# 韌性防災 API 規格書 (v1.3)

## 1. Incident

### [GET]/api/v1/incident

【輸入 (Input)】(Query Parameters):
| 參數名 | 型態 | 必填 | 說明 | 範例 |
| :--- | :--- | :--- | :--- | :--- |
| city | string | 否 | 過濾縣市 (TP/NTP) | ?city=TP |
| type | string | 否 | 過濾災情類型 | ?type=FLOOD |
| limit | int | 否 | 限制回傳筆數 (預設 50) | ?limit=20 |

【輸出 (Output)】:
| JSON 欄位名 | 型態 | 來源 | 說明 |
| :-------------- | :------- | :------- | :------------------------- |
| `ID` | int64 | 原有 | 唯一識別碼 (注意大小寫) |
| `inctype` | string | 原有 | 災情類型 (如: FLOOD) |
| `description` | string | 原有 | 詳細敘述 |
| `distance` | float64 | 原有 | 距離 |
| `latitude` | float64 | 原有 | 緯度 |
| `longitude` | float64 | 原有 | 經度 |
| `place` | string | 原有 | 地點名稱 |
| `reportTime` | datetime | 原有 | 報案時間 |
| `status` | string | 原有 | 處理狀態 |
| **`city`** | string | **新增** | 縣市 (TP/NTP) |
| **`aiSummary`** | string | **新增** | AI 生成摘要 |
| **`aiRisk`** | string | **新增** | AI 評估等級 (High/Med/Low) |

```json
{
  "ID": 1,
  "inctype": "FLOOD",
  "description": "大漢溪水位上升",
  "distance": 0,
  "latitude": 25.012,
  "longitude": 121.465,
  "place": "新北市板橋區...",
  "reportTime": "2026-04-18T14:00:00+08:00",
  "status": "open",
  "city": "NTP",
  "aiSummary": "水位即將達警戒線，請撤離低窪地區。",
  "aiRisk": "High"
}
```

## 2.Component Data

### [GET]/api/v1/component/{id}?city={city}

<<<<<<< HEAD
【輸入 (Input)】:
Path Parameter: {id} (組件識別碼，如 rain_trend, hospital_bed)
Query Parameter: city: 過濾縣市 (TP/NTP)

| 參數名 | 型態   | 必填 | 說明                               | 範例              |
| :----- | :----- | :--- | :--------------------------------- | :---------------- |
| city   | string | 否   | 過濾縣市 (TP/NTP)                  | ?city=TP          |
| sort   | string | 否   | 排序依據 (waiting_icu/waiting_bed) | ?sort=waiting_icu |

【輸出 (Output)】:

=======
>>>>>>> d75545648f12ace20bbdac025a3606677251d70f
#### (1)二維資料

> 對應Go結構：`TwoDimensionalDataOutput`

```json
{
  "data": [
    { "x": "板橋區", "y": 12.5 },
    { "x": "萬華區", "y": 8.3 }
  ]
}
```

#### (2)時間序列

> 對應Go結構：`TimeSeriesDataOutput`

<<<<<<< HEAD
=======
####(2)時間序列
>對應 Go 結構：`TimeSeriesDataOutput`
>>>>>>> d75545648f12ace20bbdac025a3606677251d70f
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
<<<<<<< HEAD
```

#### (3)三維資料

> 對應Go結構：`ThreeDimensionalDataOutput`

=======
####(3)三維資料
>對應 Go 結構：`ThreeDimensionalDataOutput`
>>>>>>> d75545648f12ace20bbdac025a3606677251d70f
```json
{
  "data": [
    {
      "name": "臺北市",
      "icon": "rain-icon",
      "data": [12, 15, 8] //代表三個行政區的數值
    },
    {
      "name": "新北市",
      "icon": "rain-icon",
      "data": [20, 25, 14]
    }
  ]
}
```

#### (4)地圖圖例資料

> 對應Go結構：`MapLegendData`

<<<<<<< HEAD
=======
####(4)地圖圖例資料
>對應 Go 結構：`MapLegendData`
>>>>>>> d75545648f12ace20bbdac025a3606677251d70f
```json
{
  "name": "一級警戒區",
  "type": "flood",
  "icon": "red-drop",
  "value": 80.5
}
```

#### (5)醫院床位資料

[GET]/api/v1/component/hospital_status

【輸出 (Output)】:

````json
{
  "status": "success",
  "data":
    {
      "city": "TP",
      "hospital_name": "台大醫院",
      "is_full_119": true,
      "metrics": {
        "waiting_consultation": 45,
        "waiting_stretcher": 12,
        "waiting_admission": 20,
        "waiting_icu": 3
      }
    }
}

## 3.qdrant

### [POST]/api/v1/qdrant/rebuild

【輸入 (Input)】:
```json
{ "force": true }
````

【輸出 (Output)】:

#### (1)成功

```json
{
  "status": "success",
  "message": "Synchronous rebuild complete (up to implemented steps).",
  "data": {
    "total_points": 100,
    "indexed_points": 50,
    "indexed_vectors": 50,
    "indexed_payloads": 50
  }
}
```

#### (2)失敗

```json
{
  "status": "error",
  "message": "qdrant rebuild is already in progress"
}
```

## websocket

### [GET]/api/v1/websocket

### [連接資訊]

- **Endpoint**:`ws://[host]/api/v1/websocket`
- **Protocol**:WebSocket(RFC 6455)
- **Authentication**:需在連線時的Header帶入`Authorization:Bearer{JWT_TOKEN}`

#### (1)伺服器主動推播訊息

```json
{
  "event": "INCIDENT_NEW",
  "timestamp": "2026-04-18T16:45:00Z",
  "payload": {
    "ID": 105,
    "inctype": "GAS_LEAK",
    "place": "新北市板橋區中正路",
    "latitude": 25.0135,
    "longitude": 121.4582,
    "aiRisk": "High",
    "aiSummary": "瓦斯濃度異常，疑似管線受損，建議立即派員切斷該區供氣。",
    "description": "民眾通報路面有異味，消防隊已出動。"
  }
}
```

#### (2)系統心跳

```json
{
  "event": "HEARTBEAT",
  "timestamp": "2026-04-18T16:50:00Z",
  "payload": {
    "status": "connected",
    "online_users": 5
  }
}
```
