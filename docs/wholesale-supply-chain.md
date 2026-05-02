# 雙北公有市場 — 批發供應鏈推演系統

## 概述

本系統透過農業部開放資料 API，即時抓取雙北批發市場交易行情（蔬果、豬肉、漁產、家禽），搭配供應鏈對應表推演 79 間公有零售市場的供貨狀態，並結合產銷履歷與 CAS 驗證資料計算「食安信任分數」。

```
┌───────────────────────────────┐
│  農業部 API（每小時抓取）        │
│  ┌─────────┐ ┌──────┐ ┌─────┐ │
│  │蔬果 A01 │ │毛豬  │ │漁產 │ │ ...
│  └────┬────┘ └──┬───┘ └──┬──┘ │
└───────┼─────────┼────────┼────┘
        ▼         ▼        ▼
 ┌──────────────────────────────┐
 │  wholesale_daily_summary     │  ← 每日批發交易聚合
 └──────────────┬───────────────┘
                ▼
 ┌──────────────────────────────┐
 │  market_supply_chain         │  ← 批發→零售 對應表
 │  (台北一 → 萬華/中正/大安…)   │
 └──────────────┬───────────────┘
                ▼
 ┌──────────────────────────────┐
 │  market_supply_status        │  ← 零售市場即時狀態
 │  supply_active, trust_score  │
 └──────────────┬───────────────┘
                ▼
        Dashboard 地圖 + 圖表
```

---

## 1. 資料來源 — 農業部 API

所有 API 來自 `https://data.moa.gov.tw/api/v1/`，需要 API Key。

### 1.1 蔬果批發交易行情（A01）

| 項目 | 說明 |
|------|------|
| Endpoint | `AgriProductsTransType/` |
| 更新頻率 | 每日（休市日無資料） |
| 日期格式 | **民國年** `115.05.02` |
| 關鍵參數 | `Start_time`, `End_time`, `MarketCode`, `limit`, `offset` |
| 分頁 | 有，`Next: true/false`，需用 `offset` 逐頁抓取 |

**回傳格式：**
```json
{
  "RS": "OK",
  "Data": [
    {
      "TransDate": "115.04.30",
      "TcType": "N04",           // N04=蔬菜, N05=水果, N06=花卉
      "CropCode": "LA1",
      "CropName": "甘藍-初秋",
      "MarketCode": "109",
      "MarketName": "台北一",
      "Upper_Price": 20.0,
      "Middle_Price": 16.5,
      "Lower_Price": 12.0,
      "Avg_Price": 16.2,         // 每公斤均價（元）
      "Trans_Quantity": 111933.0  // 交易量（公斤）
    }
  ],
  "Next": true
}
```

**雙北批發市場代碼：**

| MarketCode | 名稱 | 地址 | 主要供應範圍 |
|------------|------|------|-------------|
| `109` | 台北一（第一果菜批發市場） | 萬華區萬大路 533 號 | 南區：萬華/中正/大安/信義/文山/南港 |
| `104` | 台北二（第二果菜批發市場） | 中山區民族東路 336 號 | 北區：中山/松山/大同/內湖/北投/士林 |
| `105` | 台北市場（花卉批發） | 內湖區 | 花卉類 |

### 1.2 毛豬交易行情

| 項目 | 說明 |
|------|------|
| Endpoint | `PorkTransType/` |
| 日期格式 | 民國年**無分隔** `1150502` |
| 關鍵參數 | `limit` |

**回傳格式：**
```json
{
  "TransDate": "1150501",
  "MarketName": "新北市",
  "TransNum_Total": 2305,          // 拍賣頭數
  "TransNum_AvgWgt": 140.5,        // 平均重量(kg)
  "TransNum_AvgPrice": 84.55,      // 每公斤均價(元)
  "SpecPig_Num": 2290,             // 規格豬頭數
  "SpecPig_AvgPrice": 84.60
}
```

雙北相關：`MarketName = "新北市"`（新北市肉品市場，板橋/樹林一帶）

### 1.3 漁產品交易行情

| 項目 | 說明 |
|------|------|
| Endpoint | `FisheryProductsTransType/` |
| 日期格式 | 民國年**無分隔** `1150430` |
| 關鍵參數 | `limit`, `offset` |
| 分頁 | 有 |

**回傳格式：**
```json
{
  "TransDate": "1150430",
  "SeafoodProdCode": "1011",
  "SeafoodProdName": "金目鱸",
  "MarketName": "台北",
  "Upper_Price": 80.0,
  "Middle_Price": 77.0,
  "Lower_Price": 73.0,
  "Trans_Quantity": 2825.8,       // 交易量(公斤)
  "Avg_Price": 76.6               // 每公斤均價(元)
}
```

**雙北漁市：**

| MarketName | 說明 |
|------------|------|
| `台北` | 台北魚市（中山區，近台北二） |
| `三重` | 三重魚市（供應新北地區） |

### 1.4 家禽交易行情

| 項目 | 說明 |
|------|------|
| Endpoints | `PoultryTransType_BlackFeather/`（黑羽土雞）、`PoultryTransType_RedFeather/`（紅羽）、`PoultryTransType_BoiledChicken_Eggs/`（白肉雞/雞蛋） |
| 日期格式 | 西元 `2026/04/30` |
| 特性 | **全國統一報價**，無分市場 |

**回傳格式（黑羽土雞範例）：**
```json
{
  "TransDate": "2026/04/30",
  "LunarCalendar": "十三",
  "BlackFeather_S_M": "53.0",    // 公雞價(元/台斤)
  "BlackFeather_S_F": "53.0"     // 母雞價(元/台斤)
}
```

### 1.5 產銷履歷檢驗結果

| 項目 | 說明 |
|------|------|
| Endpoint | `SalesResumeAgriproductsResultsType/` |
| 用途 | 計算 Trust Score 的合格率 |

**回傳格式：**
```json
{
  "Number": "TGAP1140500065",
  "SamplingDate": "1141211",
  "ProductName": "茭白筍-履歷茭白筍",
  "ProducerName": "陳泰鈞",
  "SamplingLocation": "臺北市中山區龍江路15號",  // ← 台北一地址
  "InspectResult": "合格",                      // "合格" / "不合格"
  "Note": "標示合格"
}
```

### 1.6 CAS 驗證產品

| 項目 | 說明 |
|------|------|
| Endpoint | `CASProductInquiryType/` |
| 用途 | 計算 Trust Score 的 CAS 覆蓋率 |

**回傳格式：**
```json
{
  "Emblem_ID": "010101",
  "Factory_CName": "台灣農畜產工業股份有限公司",
  "Factory_Address": "屏東縣屏東市建國路480號",
  "Material_Name": "肉品",
  "PType_Name": "冷藏豬肉",
  "Product_Name": "冷藏豬肉"
}
```

---

## 2. 資料庫 Schema

所有表在 `postgres-data` 的 `dashboard` 資料庫中。

### 2.1 `wholesale_daily_summary` — 批發交易日報

| 欄位 | 型別 | 說明 |
|------|------|------|
| `data_date` | text | 民國日期 `115.05.02` |
| `market_code` | text | 批發市場代碼（`109`, `104`, `新北市`, `台北`, `三重`, `NATIONAL`） |
| `market_name` | text | 批發市場名稱 |
| `category` | text | `vegetable_fruit` / `pork` / `fishery` / `poultry` |
| `total_items` | integer | 當日交易品項數 |
| `total_quantity` | float | 當日交易總量（kg 或頭數） |
| `avg_price` | float | 加權平均價格 |
| `top_items` | jsonb | 前 5 大品項 `[{"name":"甘藍","qty":111933,"price":16.2}]` |
| `fetched_at` | timestamptz | 資料抓取時間 |

### 2.2 `market_supply_chain` — 供應鏈對應表

| 欄位 | 型別 | 說明 |
|------|------|------|
| `wholesale_code` | text | 批發市場代碼 |
| `wholesale_name` | text | 批發市場名稱 |
| `wholesale_category` | text | 供應類別 |
| `retail_table` | text | `public_market_tpe` 或 `public_market_new_tpe` |
| `retail_name` | text | 零售市場名稱 |
| `retail_district` | text | 行政區 |
| `match_reason` | text | 對應理由（如「地理鄰近（南區）+ 蔬果攤位」） |

**對應邏輯：**
- **蔬果**：台北一 → 南區 6 區有蔬果攤的市場；台北二 → 北區 6 區；台北一 → 全部新北市場
- **豬肉**：新北市肉品市場 → 有獸肉攤位（`meat > 0`）的台北市場 + 全部新北市場
- **漁產**：台北魚市 → 有漁產攤位（`seafood > 0`）的台北市場；三重魚市 → 全部新北市場
- **家禽**：全國統一行情 → 有家禽攤位（`poultry > 0`）的台北市場

### 2.3 `market_supply_status` — 零售市場供應狀態

| 欄位 | 型別 | 說明 |
|------|------|------|
| `retail_table` | text | 來源表 |
| `retail_name` | text | 市場名稱 |
| `retail_district` | text | 行政區 |
| `supply_active` | boolean | 今日是否有供貨 |
| `supply_categories` | text[] | 有供貨的類別陣列 `{vegetable_fruit,pork}` |
| `total_items` | integer | 關聯的供應品項總數 |
| `total_quantity` | float | 關聯的供應總量 |
| `top_items` | jsonb | 前 5 大關聯品項 |
| `trust_score` | float | 0~100 信任分數 |
| `trust_detail` | jsonb | `{"traceability_rate":99.1, "cas_coverage":100}` |
| `status_text` | text | 前端顯示文字 |
| `updated_at` | timestamptz | 最後更新時間 |

---

## 3. Trust Score 計算公式

```
Trust Score = 0.6 × traceability_rate + 0.3 × cas_coverage + 0.1 × base_score

其中：
- traceability_rate (0~100): 產銷履歷檢驗合格率
  = (雙北採樣地點的合格筆數 / 雙北採樣總筆數) × 100

- cas_coverage (0~100): CAS 認證產品覆蓋率
  = min(CAS 肉品認證數 / 10, 1.0) × 100

- base_score: 固定 50（有供貨時給予基礎分）

- 無供貨時 trust_score = 0
```

**範例**：合格率 99.1%、CAS 產品 1000+ → `0.6 × 99.1 + 0.3 × 100 + 0.1 × 50 = 94.5`

---

## 4. ETL 流程

**DAG**：`wholesale_supply_chain`
**排程**：每小時（`0 */1 * * *`）
**路徑**：`dags/proj_city_dashboard/wholesale_supply_chain/wholesale_supply_chain.py`

### 流程步驟

1. **抓取批發資料**：平行呼叫 4 類 API（蔬果需分頁）
2. **聚合寫入**：依市場 × 類別 聚合為 `wholesale_daily_summary`
3. **抓取信任資料**：產銷履歷 + CAS 驗證
4. **計算 Trust Score**
5. **更新零售狀態**：JOIN `wholesale_daily_summary` × `market_supply_chain` → UPSERT `market_supply_status`

### 注意事項

- 蔬果 API 日期用**民國年帶點** `115.05.02`
- 豬肉/漁產 API 日期用**民國年無分隔** `1150502`
- 家禽 API 日期用**西元** `2026/05/02`
- 休市日（週日/國定假日）所有 API 回傳空或「休市」
- API 有 rate limit，建議每支間隔 1 秒

---

## 5. 前端視覺化

### 組件：`wholesale_supply_chain`（市場供應鏈）

- **圖表**：BarChart + DonutChart，顯示「已供貨 / 未供貨」市場數量
- **地圖**：circle 類型
  - **顏色**：綠色 `#2ECC71`（已供貨）/ 紅色 `#E74C3C`（未供貨/休市）
  - **圓圈大小**：依 `trust_score` 插值（0→4px, 50→7px, 90→11px）
  - **tooltip**：市場名稱、行政區、供貨類別、供應品項數、信任分數、供應狀態

### GeoJSON 檔案

| 檔案 | 來源 | features |
|------|------|----------|
| `mapData/supply_chain_tpe.geojson` | `public_market_tpe` × `market_supply_status` | 49 |
| `mapData/supply_chain_new_tpe.geojson` | `public_market_new_tpe` × `market_supply_status` | 30 |

### GeoJSON properties 欄位

```json
{
  "name": "環南中繼市場",
  "district": "萬華區",
  "supply_active": true,
  "supply_categories": "vegetable_fruit, fishery",
  "total_items": 335,
  "trust_score": 94.5,
  "status_text": "今日新鮮物資已由批發市場供應",
  "top_items_display": "甘藍-初秋 111933kg、鳳梨-金鑽鳳梨 39376kg"
}
```

---

## 6. 儀表板配置

供應鏈組件（id=223）已加入「食安健康」儀表板（`food_safety_health_tpe`）。

組件配置 SQL：`db-sample-data/wholesale_supply_chain_component.sql`

---

## 7. API Key

| 平臺 | Key | 用途 |
|------|-----|------|
| 農業部開放資料 | `C4QN6C4WX4KP9XONGGIFSHOBUUTLX9` | 所有批發/履歷/CAS API |

---

## 8. 相關檔案一覽

| 檔案 | 說明 |
|------|------|
| `dags/proj_city_dashboard/wholesale_supply_chain/job_config.json` | DAG 設定 |
| `dags/proj_city_dashboard/wholesale_supply_chain/wholesale_supply_chain.py` | ETL 主程式 |
| `db-sample-data/wholesale_supply_chain_component.sql` | 組件配置 SQL |
| `Taipei-City-Dashboard-FE/public/mapData/supply_chain_tpe.geojson` | 台北地圖資料 |
| `Taipei-City-Dashboard-FE/public/mapData/supply_chain_new_tpe.geojson` | 新北地圖資料 |
| `docs/wholesale-supply-chain.md` | 本文件 |
