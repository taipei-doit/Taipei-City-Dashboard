# 災前情境劇本庫——可行性研究報告

> **版本**：v1.0 | **日期**：2026-04-08 | **用途**：黑客松備賽 + 內部決策
> **收件人**：開發團隊（主）、雙北黑客松評審（輔）

---

## 0. 一頁式摘要

| 項目 | 內容 |
|------|------|
| **題目核心** | 復合災難（颱風+淹水+地震）的預製情境劇本庫，支援市政決策層在災前完成資源調度決策 |
| **使用者** | 應變指揮官、局處長/科長、台北大數據中心工程師 |
| **系統三層** | 台北城市儀表板（Vue 前端）+ MiroFish（輿情模擬）+ MATSim（交通疏散，靜態預跑）|
| **黑客松 MVP** | 預製 3-5 個復合災難劇本，點選展開風險地圖 + 輿情預測 + 疏散建議 + 決策卡片 |
| **AI 定位** | 摘要、比較、決策建議草稿——不做預測、不做黑箱打分 |
| **資料來源** | data.taipei、data.ntpc.gov.tw、CWA、TDX、NCDR |
| **PR 策略** | schema → dashboard widgets → adapters，分三批回貢獻官方 repo |

---

## 1. 問題定義與背景

### 1.1 核心問題

雙北在面對復合災難（如颱風伴隨淹水、地震引發火警）時，政府官員面臨：

- **資訊碎片化**：氣象、交通、避難、輿情分屬不同系統，無法在一個畫面整合
- **決策延遲**：缺乏「預製劇本」，每次都要臨時整合資料，造成黃金應變時間流失
- **副作用盲區**：下達指令（如關閉水門、發布撤離令）的連鎖副作用缺乏可視化

### 1.2 解決方向

建立「災前情境劇本庫」：
- **預製 3-5 個復合災難情境**，預先整合所有相關資料與模擬結果
- 指揮官點選劇本，**30 秒內**看到完整風險地圖 + 決策建議 + 副作用警告
- 輿情模擬（MiroFish）預測社會反應，交通疏散（MATSim）提供路徑建議

### 1.3 雙北共融價值

- 整合 data.taipei + data.ntpc.gov.tw 跨域資料
- 跨河走廊（中正橋、忠孝橋）疏散路徑同時涉及台北市與新北市
- 符合競賽「Metro-Taipei」資料架構要求

---

## 2. 使用者分析

### 2.1 主要使用者

| 角色 | 需求 | UX 重點 |
|------|------|---------|
| **應變指揮官** | 視覺化直覺、低認知負荷、快速決策 | 3 個核心 KPI，一頁決策摘要 |
| **局處長/科長** | 細節資料（淹水深度、收容所空位率）、資源調度 | 可展開的細節層、異常警示 |
| **TBDC 工程師** | 穩定 API 接口、結構化資料標準、可維護架構 | OpenAPI spec、模組化設計 |

### 2.2 User Journey：颱風應變決策路徑

#### Phase 1 — 預警期（T-72h）：風險感知
- **官員看什麼**：氣象路徑預測、歷史相似颱風淹水範圍對照、最糟/最機率情境比較
- **決策需求**：是否提前整備物資？哪些地區需要預防性撤離？
- **劇本庫支援**：自動比對歷史相似案例，生成「預警摘要」

#### Phase 2 — 整備期（T-24h）：資源調度
- **官員看什麼**：即時感測器狀態、避難所空位率、各區脆弱人口地圖
- **決策需求**：機具是否到位？收容所人力是否進駐？是否宣布停班停課？
- **劇本庫支援**：物資缺口計算、機具預置建議、異常狀態警示

#### Phase 3 — 登陸前（T-0）：決策執行
- **官員看什麼**：潮汐+河川水位連動圖、疏散門監控、疏散完成率
- **決策需求**：關閉水門時間、強制撤離令發布
- **劇本庫支援**：關鍵決策節點倒數、動態撤離路徑

#### Phase 4 — 應變中（Response）：損害控管
- **官員看什麼**：119/110 報案熱點、即時災情通報地圖、道路中斷狀況
- **決策需求**：救災資源配置、停電/停水修復優先順序
- **劇本庫支援**：決策建議卡片、副作用可視化

---

## 3. 系統架構

### 3.1 三層架構概覽

```
[使用者：指揮官 / 局處長 / 工程師]
        │
        ▼
[台北城市儀表板 / Vue 前端]
  ├─ 劇本選擇器（Scenario Selector）
  ├─ 風險地圖（Mapbox 疊圖）
  ├─ 時間軸回放（T-72h → 應變中）
  ├─ 輿情面板（民意熱度、謠言擴散）
  ├─ 疏散面板（路徑、瓶頸、完成率）
  └─ 決策卡片（建議行動 + 副作用警告）
        │ RESTful API / SSE
        ▼
[Scenario Orchestrator — 中介整合層]
  ├─ 劇本庫服務（查表、版本控管）
  ├─ MiroFish Adapter
  ├─ MATSim Adapter
  └─ 結果整併器（decision_package）
        │
  ┌─────┴─────┐
  ▼           ▼
[MiroFish]  [MATSim]
 輿情模擬    交通疏散
 GraphRAG   靜態預跑
 多智能體    路網查表
        │
        ▼
[資料層]
  ├─ 劇本 JSON 儲存
  ├─ GraphRAG 向量庫
  ├─ MATSim 預跑結果
  ├─ 雙北開放資料快取
  └─ 稽核/版本記錄
```

### 3.2 各層職責與黑客松策略

| 層 | 技術 | 黑客松策略 | 可行性 |
|----|------|-----------|--------|
| **前端** | Vue + Apexcharts + Mapbox | 完整實作，台北城市儀表板框架 | ✅ 高 |
| **中介層** | Go + Gin（配合官方技術棧）| 劇本查表 API + 結果整併 | ✅ 高 |
| **MiroFish** | Python + FastAPI + Docker | Docker 起來，輕量種子測試 | ⚠️ 中 |
| **MATSim** | Java + 預跑結果 JSON | 預跑靜態結果，假接口查表 | ⚠️ 中（需提前跑） |
| **資料層** | PostgreSQL + Redis + JSON | 雙北開放資料 + 合成 proxy | ✅ 高 |

---

## 4. 開放資料盤點

### 4.1 核心資料源清單

| 類別 | 資料名稱 | 平台/ID | 格式 | 更新頻率 | API |
|------|---------|---------|------|---------|-----|
| **預警** | 氣象預報觀測（雷達、雨量） | 中央氣象署 CWA | JSON | 即時（10-60min） | ✅ opendata.cwa.gov.tw |
| **地震** | 地震速報/各區震度 | CWA E-A0015-001 | JSON | 秒級（觸發式） | ✅ CWA Earthquake API |
| **淹水** | 雙北即時淹水感測 | data.taipei e73305a4 | JSON | 即時（10min） | ✅ |
| **避難** | 臺北市避難收容處所 | data.taipei aaf97773 | JSON/CSV | 每年 | ✅ |
| **避難** | 新北市避難收容處所 | data.ntpc 25E439AB | JSON/XML | 每年 | ✅ |
| **人口** | 臺北市各區人口年齡 | data.taipei 64c8a3a0 | CSV | 每月 | ✅ |
| **人口** | 臺北市扶養比及老化指數 | data.taipei aafb15dc | CSV | 每年 | ✅ |
| **人口** | 新北市現住人口年齡 | data.ntpc 8308AB58 | CSV | 每月 | ✅ |
| **交通** | 雙北道路封閉/即時交通 | TDX 平台 | JSON | 即時（5min） | ✅ tdx.transportdata.tw |
| **歷史災害** | 歷年淹水點/災損 | NCDR | GeoJSON | 歷史存檔 | ✅ web.ncdr.nat.gov.tw |
| **歷史災害** | 遭受災害救助情形（新北） | data.ntpc 05e9a748 | CSV | 年度 | ✅ |

### 4.2 三種輸入種子設計

| 種子類型 | 來源 | 用途 |
|---------|------|------|
| **過去資料** | 歷史災害新聞、NCDR 紀錄、納莉/蘇迪勒颱風案例 | MiroFish GraphRAG 歷史語境 |
| **現在資料** | CWA、data.taipei、TDX 即時 API | 劇本觸發條件、即時圖層 |
| **未來合成 proxy** | 預製「假設性復合災難情境文件」 | MiroFish 未來情境推演種子 |

### 4.3 資料 Join 路徑

```
避難收容處所（地理坐標）
    ↕ 地理空間 Join（行政區）
人口脆弱性（老化指數、身障分布）
    ↕ 行政區 Join
即時淹水感測 + 歷史淹水範圍
    ↕ 事件驅動 Trigger
劇本定義 JSON → 啟動 MiroFish + MATSim 查表
```

---

## 5. MiroFish 輿情模擬整合

### 5.1 GraphRAG 種子資料結構

**節點類型**：`Hazard`、`Location`、`Facility`、`Road`、`Actor`、`Rumor`、`Policy`

**邊類型**：`affects`、`located_at`、`blocked_by`、`spreads_to`、`recommends`

### 5.2 模擬角色

- 市民（一般、高齡、身障）
- 媒體記者
- 官方發言人
- 里長/社群意見領袖
- 專家顧問

### 5.3 輸出格式

```json
{
  "scenario_id": "tw-typhoon-flood-001",
  "time_series": [
    {
      "time": "T+0",
      "sentiment_index": 0.52,
      "rumor_index": 0.21,
      "top_topics": ["停電", "淹水", "撤離"]
    }
  ],
  "rumor_clusters": [
    {
      "topic": "橋梁是否受損",
      "spread_score": 0.74,
      "source_trace": ["media", "citizen"]
    }
  ],
  "recommended_official_message": [
    "請依指定路線疏散，勿使用XX橋",
    "請勿轉傳未經證實資訊"
  ],
  "confidence": 0.68
}
```

---

## 6. MATSim 交通疏散整合

### 6.1 黑客松可行範圍

| 項目 | 規格 |
|------|------|
| **路網範圍** | 台北核心區 + 1-2 條跨河走廊（中正橋/忠孝橋） |
| **連結數** | 200-500 links |
| **節點數** | 100-300 nodes |
| **劇本數** | 3-5 個，離線預跑 |
| **線上行為** | 只讀預跑結果，不重新計算 |

### 6.2 靜態預跑策略

- 賽前針對每個劇本離線跑完 MATSim
- 保存關鍵指標：疏散完成率、平均旅行時間倍數、壅塞瓶頸、建議替代路徑
- 線上展示時透過假接口查表輸出

### 6.3 假接口設計

```
GET /api/matsim/result?scenario_id=tw-typhoon-flood-001
→ 疏散完成率、平均時間倍數、壅塞路段

GET /api/matsim/bottlenecks?scenario_id=...
→ 受阻路段清單、建議替代走廊

GET /api/matsim/layers?scenario_id=...
→ Mapbox 圖層 refs（heatmap、bottlenecks、corridors）
```

---

## 7. 劇本庫 Schema 設計

### 7.1 預製劇本清單

| ID | 標題 | 災害類型 | 聚焦區域 |
|----|------|---------|---------|
| `tw-typhoon-flood-001` | 強颱 + 淡水河氾濫 + 大安停電 | 颱風、淹水、停電 | 大安、萬華、板橋 |
| `tw-earthquake-fire-001` | 地震 + 火警 + 主幹道中斷 | 地震、火災、交通 | 台北核心 + 跨河走廊 |
| `tw-typhoon-surge-001` | 颱風 + 大潮 + 捷運停駛 | 颱風、潮汐、交通 | 淡水線沿線 |
| `tw-compound-heatwave-001` | 颱風過後熱浪 + 停水 | 熱浪、停水 | 雙北全域 |
| `tw-earthquake-flood-001` | 地震 + 豪雨複合 + 土石流 | 地震、土石流 | 新店、烏來、汐止 |

### 7.2 劇本 JSON Schema

```json
{
  "scenario_id": "tw-typhoon-flood-001",
  "version": "1.0.0",
  "title": "強颱 + 淡水河氾濫 + 大安停電",
  "status": "ready",
  "region": {
    "city": ["Taipei", "NewTaipei"],
    "focus_area": "Danshui River Corridor + Da'an District",
    "ct": "Metro-Taipei"
  },
  "hazards": [
    { "type": "typhoon", "severity": 5, "start_time": "T+0" },
    { "type": "flood", "severity": 4, "start_time": "T+60" },
    { "type": "power_outage", "severity": 3, "start_time": "T+90" }
  ],
  "timeline": [
    { "time": "T+0", "event": "颱風登陸，風速 > 50 m/s" },
    { "time": "T+60", "event": "淡水河水位超警戒，水門關閉" },
    { "time": "T+90", "event": "大安區大規模停電" }
  ],
  "simulations": {
    "mirofish": {
      "seed_bundle_id": "seed-typhoon-2026",
      "output_ref": "mirofish://results/tw-typhoon-flood-001"
    },
    "matsim": {
      "network_profile": "taipei_danshui_corridor",
      "output_ref": "matsim://results/tw-typhoon-flood-001"
    }
  },
  "ui_defaults": {
    "default_view": "decision_maker",
    "map_layers": ["flood_risk", "bottleneck", "shelter", "power_outage"]
  },
  "metadata": {
    "created_at": "2026-04-08T00:00:00+08:00",
    "author": "hackathon-team"
  }
}
```

---

## 8. 儀表板 UX 設計

### 8.1 首頁佈局（戰情室模式）

```
┌────────────────────────────────────────────────────┐
│  左側：KPI 指標        中央：3D 地圖          右側：決策流  │
│  ─ 總報案數            ─ 淹水範圍疊圖        ─ 3h 風險趨勢 │
│  ─ 淹水警戒區數         ─ 避難所分布         ─ 輿情熱度    │
│  ─ 水門關閉狀況         ─ 疏散路徑           ─ 謠言擴散    │
│  ─ 停電戶數            ─ 脆弱人口熱力圖      ─ 官方話術建議 │
└────────────────────────────────────────────────────┘
│  下方：時間軸（T-72h ────────────────── T+應變中）   │
└────────────────────────────────────────────────────┘
```

### 8.2 劇本選擇介面

- **卡片式切換**：5 張劇本卡，每張顯示災害類型圖示 + 風險等級 + 受影響人口數
- **點選後進入模擬模式**：地圖自動切換到對應劇本的預計淹水範圍與疏散路徑
- **What-If 時間軸**：拉動 Slider 查看 T+1/3/6 小時推估災情

### 8.3 決策建議卡片格式

```
┌─────────────────────────────────────────┐
│ 🔴 高優先：關閉中正橋車道                 │
│ 依據：MATSim 預測 T+30min 壅塞達 95%    │
│        + 淡水河水位 > 7.3m（警戒值）     │
│ 預計效果：疏散效率提升 23%              │
│ ⚠️ 副作用：板橋往台北車流移至忠孝橋     │
│           → 忠孝橋負荷增加 40%          │
│ [追蹤執行進度]                          │
└─────────────────────────────────────────┘
```

### 8.4 副作用可視化

- 游標 hover 決策卡 → 地圖同步高亮受影響路段/區域
- 副作用以**橙色警示層**疊加在地圖上
- 信心指數以 `(0.68)` 標示，來源可追溯

---

## 9. 技術風險評估

### 9.1 前端層

| 風險 | 描述 | 對策 |
|------|------|------|
| 資訊過載 | 市政層看不懂大量模擬輸出 | 預設只顯示 3-5 KPI，細節折疊 |
| 地圖效能 | 疊圖太多造成卡頓 | 圖層分級載入、預渲染 heatmap |
| 錯誤解讀 | 使用者把推演結果當真實預測 | 界面明顯標示「情境推演」+ 信心區間 |

### 9.2 MiroFish 層

| 風險 | 描述 | 對策 |
|------|------|------|
| 輸出不穩定 | LLM 幻覺造成不一致結果 | GraphRAG 嚴格檢索 + 模板化輸出 |
| 來源不可追溯 | 難以交代輿情依據 | 每條結論保留 `source_trace` |
| 角色失真 | 市民反應過於理想化 | 行為規則先簡化，以趨勢展示為主 |

### 9.3 MATSim 層

| 風險 | 描述 | 對策 |
|------|------|------|
| 路網過大 | 48h 內無法完成資料清理與預跑 | 只做小範圍關鍵走廊（200-500 links） |
| 校準不足 | 結果與真實交通差距大 | 明確定位為「示範性靜態推演」，不主張精準預測 |
| 劇本變化無法對應 | 當天題目變化時無預跑結果 | 預製 5 個覆蓋率高的通用劇本 |

---

## 10. 黑客松 48 小時執行時序

| 時段 | 任務 |
|------|------|
| **0-4h** | 鎖定 5 個劇本、定義 JSON schema、決定路網範圍、確認前端版型 |
| **4-12h** | 建劇本庫雛形、整理 GraphRAG 種子資料、匯入路網 POI、定義 API contract |
| **12-24h** | 跑 MiroFish 預演算（或半手工輸出）、產出 MATSim 靜態結果、完成查表邏輯 |
| **24-36h** | 完成 Vue 儀表板、串接三層 API、完成地圖 + 時間軸展示 |
| **36-44h** | 調整 KPI 表示、加上來源追溯、修正格式不一致 |
| **44-48h** | Demo 腳本、備援截圖、最終驗收 |

---

## 11. AI 功能邊界

### AI 可以做
- 摘要儀表板狀態（「目前大安區風險最高，建議優先支援」）
- 比較劇本差異（「劇本 A vs B：A 的疏散壓力高 30%」）
- 生成官方話術建議草稿
- 解釋決策建議依據（「因為 X 資料顯示...」）

### AI 不可以做
- 預測個人安危或特定地址損失
- 不可追溯來源的黑箱風險評分
- 取代政府政策規則或法定決策程序
- 聲稱模擬結果等同真實災害預測

---

## 12. PR 整併策略

### 分批回貢獻官方 repo 順序

1. **schema PR**（最先、最易接受）：JSON schema、TypeScript types、驗證器
2. **dashboard widgets PR**：地圖、時間軸、KPI 卡片、決策摘要元件
3. **adapters PR**：MiroFishAdapter、MATSimAdapter（包成獨立模組）
4. **sample scenarios PR**：5 個範例劇本 + 預跑結果

### 合併原則
- 不破壞既有 API
- 以 feature flag 控制新功能
- 保留 mock / real 兩種模式
- 所有輸出標準化成 `decision_package`
- AGPL 授權，賽後 2 個月內完成

---

## 13. 資料清理流程

### 13.1 資料來源分層

```
Layer A — 即時觸發資料（API，每 5-60min 更新）
  CWA 氣象 API       → 颱風路徑、雷達回波、雨量
  CWA 地震 API       → 震度分布、速報
  data.taipei 淹水    → 即時感測水位（e73305a4）
  TDX 交通            → 道路封閉、壅塞程度

Layer B — 靜態參考資料（年度/季度更新，預先下載）
  臺北避難收容        → aaf97773（JSON）
  新北避難收容        → 25E439AB（JSON）
  臺北人口年齡        → 64c8a3a0（CSV）
  臺北老化指數        → aafb15dc（CSV）
  新北人口年齡        → 8308AB58（CSV）

Layer C — 歷史種子資料（一次性匯入，給 MiroFish）
  NCDR 歷史災損      → GeoJSON（歷年淹水點、土石流）
  新北災害救助紀錄    → 05e9a748（CSV）
  颱風歷史新聞        → 人工收集（納莉 2001、蘇迪勒 2015）
```

### 13.2 資料清理步驟（Python）

#### Step 1 — 拉取與快取（ETL 入口）

```python
# 每次劇本初始化時執行
sources = {
    "shelter_taipei":  "https://data.taipei/api/getDatasetInfo?id=aaf97773...",
    "shelter_ntpc":    "https://data.ntpc.gov.tw/api/datasets/25E439AB...",
    "population_age":  "https://data.taipei/api/getDatasetInfo?id=64c8a3a0...",
    "flood_sensor":    "https://data.taipei/api/getDatasetInfo?id=e73305a4...",
    "cwa_typhoon":     "https://opendata.cwa.gov.tw/api/v1/rest/datastore/...",
    "tdx_traffic":     "https://tdx.transportdata.tw/api/basic/...",
}
# 快取到 PostgreSQL，標記 source、fetched_at、layer
```

#### Step 2 — 地理編碼標準化

```python
# 問題：各來源用不同地理單位
#   避難收容 → 地址字串
#   人口資料 → 行政區名稱
#   淹水感測 → 經緯度座標
#   TDX 交通 → 路段 ID

# 統一做法：全部轉為 WGS84 經緯度 + 行政區碼（5碼）
# 工具：geopy（地址 → 座標）、shapely（點在哪個行政區）
```

#### Step 3 — 欄位對映與驗證

```python
# 避難收容 schema 清理
shelter_schema = {
    "id":       str,          # 處所代碼
    "name":     str,          # 名稱
    "district": str,          # 行政區（5碼）
    "lat":      float,
    "lng":      float,
    "capacity": int,          # 容納人數
    "city":     "Taipei" | "NewTaipei"
}

# 人口脆弱性 proxy 計算
vulnerability_score = (
    老化指數 * 0.4 +
    身障人口比率 * 0.3 +
    獨居老人比率 * 0.3
)
```

#### Step 4 — Join 路徑執行

```python
# 核心 Join：避難缺口計算
df = (
    population_by_district      # 各區人口 + 脆弱性 proxy
    .merge(shelter_by_district, on="district_code")  # 各區收容容量
    .assign(gap=lambda x: x["vulnerable_pop"] - x["total_capacity"])
)
# gap > 0 → 收容缺口，標記為高優先劇本觸發條件
```

#### Step 5 — 合成 Proxy 資料（未來情境種子）

```python
# 針對每個劇本，生成假設性情境描述文件
# 例：劇本 A「強颱 + 淡水河氾濫」
proxy_doc = {
    "scenario_id": "tw-typhoon-flood-001",
    "hypothetical_events": [
        "淡水河水位於 T+60min 超過 7.3m 警戒值",
        "中正橋、忠孝橋雙向封閉",
        "大安區 3 萬戶停電"
    ],
    "seed_for": "mirofish"  # 作為 MiroFish 輸入種子
}
```

#### Step 6 — 輸出至資料層

```python
# 結果寫入 PostgreSQL
# 對應儀表板 3.0 的四張表架構：
#   Component        → 劇本組件定義
#   Query Chart (CT="Metro-Taipei") → 雙北查詢設定
#   Component Chart  → 共用圖表樣式
#   Component Maps   → 地圖圖層設定
```

### 13.3 資料品質注意事項

| 問題 | 說明 | 處理方式 |
|------|------|---------|
| **顆粒度不一致** | 人口資料是區級，淹水感測是點位 | 統一聚合到區級，避免假精度 |
| **更新頻率落差** | 年度人口 vs 即時水位 | 分層快取，靜態 + 即時雙軌 |
| **避難所地址模糊** | 部分只有中文地址無座標 | geopy 地理編碼 + 人工驗證抽查 |
| **雙北欄位命名不一致** | 台北/新北各自命名規則 | 統一 mapping table，標記 city 欄位 |
| **合成資料標記** | 未來 proxy 情境非真實資料 | 一律標記 `is_synthetic: true`，前端顯示警示 |

---

## 附錄：系統整合資料流

```
雙北開放資料（CWA/TDX/data.taipei/NCDR）
    ↓ 資料清理（Python）
劇本觸發條件評估
    ↓ 劇本 JSON 查表
Scenario Orchestrator
    ├── MiroFish Adapter → 輿情時間序列
    └── MATSim Adapter  → 疏散路徑結果
    ↓ decision_package 整合
Vue 儀表板
    ├── 決策卡片（建議行動 + 副作用）
    ├── Mapbox 地圖疊圖
    └── Apexcharts 時間軸圖表
```
