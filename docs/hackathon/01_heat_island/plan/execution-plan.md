# 執行計畫 v1.0

> **日期**：2026-04-15
> **狀態**：規劃中，尚未執行
> **對應組件規格**：13-component-specs.md

---

## 任務 A：資料源驗證

**目標**：確認 10 個組件的核心資料集真的可以打 API 拿到、格式正確、欄位存在。

### 驗證清單

| 優先 | 組件 | 資料集名稱 | 平台 | 資料 ID | 格式 | 待確認事項 |
|------|------|-----------|------|---------|------|-----------|
| 🔴 高 | 組件 9 | 即時淹水感測 | data.taipei | e73305a4 | JSON | 即時更新頻率、欄位名稱、座標格式 |
| 🔴 高 | 組件 2 | 景點人潮即時燈號 | data.taipei | 待查 | JSON | API endpoint 是否公開、更新頻率 |
| 🔴 高 | 組件 5 | 全國急診即時資訊 | 衛福部 | 待查 | JSON | 更新頻率、是否含壅塞度欄位 |
| 🔴 高 | 組件 4 | 台北 AED 設置地點 | data.taipei | 待查 | CSV | 座標欄位（緯度/經度）是否直接存在 |
| 🟡 中 | 組件 4 | 新北 AED 設置資訊 | data.ntpc | 待查 | JSON | 欄位格式是否與台北一致 |
| 🟡 中 | 組件 8 | 台北避難收容處所 | data.taipei | aaf97773 | JSON | 容量欄位、座標格式 |
| 🟡 中 | 組件 8 | 新北避難收容處所 | data.ntpc | 25E439AB | JSON | 欄位是否與台北對齊 |
| 🟡 中 | 組件 8 | 台北各區人口年齡 | data.taipei | 64c8a3a0 | CSV | 行政區碼格式、65歲以上欄位 |
| 🟡 中 | 組件 1 | 藝文活動 | opendata.culture.tw | 待查 | JSON | API 是否有雙北分區篩選 |
| 🟢 低 | 組件 6 | 台北食品稽查 | data.taipei | 待查 | CSV | 稽查結果欄位（合格/違規）、時間欄位 |
| 🟢 低 | 組件 3 | 台北藝文館所 | data.taipei | 待查 | JSON | 館所類型欄位、座標 |

### 驗證方法（待執行）

```bash
# 範例：驗證淹水感測 API
curl "https://data.taipei/api/getDatasetInfo?id=e73305a4&scope=resourceAquire&limit=5" | jq .

# 驗證回傳：
# 1. HTTP 200？
# 2. 有幾筆資料？
# 3. 欄位清單是什麼？
# 4. 座標欄位格式（WGS84 or TWD97）？
# 5. 更新時間戳記？
```

### 驗證結果紀錄

> **初步驗證已執行（2026-04-15）** — 詳細表格見 [`15-source-validation-results.md`](./15-source-validation-results.md)。
> 新北收容與人口 API 已回傳可用 JSON；data.taipei 舊版 `getDatasetInfo` endpoint 對已知 ID 回傳 404，需改用目前資料集頁面的 API preview/download URL 進一步驗證。Hackathon demo 先採 mock/static fallback，並保留 source trace，不把 mock 資料宣稱為即時官方讀值。

| 資料集 | 狀態 | 筆數 | 關鍵欄位 | 座標格式 | 備注 |
|--------|------|------|---------|---------|------|
| 即時淹水感測 | ❓ 待驗 | — | — | — | — |
| 景點人潮燈號 | ❓ 待驗 | — | — | — | — |
| 急診即時資訊 | ❓ 待驗 | — | — | — | — |
| 台北 AED | ❓ 待驗 | — | — | — | — |
| 新北 AED | ❓ 待驗 | — | — | — | — |
| 台北避難收容 | ❓ 待驗 | — | — | — | — |
| 新北避難收容 | ❓ 待驗 | — | — | — | — |
| 台北人口年齡 | ❓ 待驗 | — | — | — | — |
| 藝文活動 | ❓ 待驗 | — | — | — | — |
| 食品稽查 | ❓ 待驗 | — | — | — | — |

### 若驗證失敗的備案

| 資料集 | 備案 |
|--------|------|
| 景點人潮燈號（若 API 不公開） | 改用 mock 資料模擬，前端介面仍完整 |
| 急診即時資訊（若無壅塞度） | 改用就醫院所清冊 + 靜態容量估算 |
| 新北 AED（若欄位不對齊） | 人工清理欄位對應表 |

---

## 任務 B：前端 Wireframe

**目標**：畫出每個組件的 layout，確認視覺邏輯和互動流程，讓前端開發有明確依據。

**技術限制**：
- 圖表只能用 Apexcharts（禁用其他第三方圖表庫）
- 地圖用 Mapbox GL JS
- 下拉切換台北/雙北是每個組件的必要元素

### 組件 Layout 規格

#### 組件 1：藝文活動即時地圖

```
┌──────────────────────────────────────────────────────┐
│ [城市切換: 台北 ▼] [日期: 今天 | 本週末 | 本週 | 自訂] │
│ [類型: ✅音樂 ✅展覽 ✅市集 □戲劇 □親子]              │
├─────────────────────────┬────────────────────────────┤
│                         │  各區活動數量              │
│   Mapbox 地圖           │  ColumnChart               │
│   - 活動點位（色標）     │  (台北 vs 新北 雙色)       │
│   - 點擊 → 活動卡片彈窗  │                            │
│                         │  AI 洞察面板               │
│                         │  「本週末亮點摘要...」      │
└─────────────────────────┴────────────────────────────┘
```

**互動流程**：
1. 預設顯示「今天、台北、全部類型」
2. 切換城市 → 地圖和圖表同步更新
3. 切換日期 → 地圖點位更新
4. 點擊類型 tag → 過濾地圖點位
5. 點擊地圖 pin → 右側展開活動詳情卡片
6. 點擊「AI 摘要」按鈕 → 呼叫 LLM 生成本週亮點

---

#### 組件 2：景點人潮即時燈號

```
┌──────────────────────────────────────────────────────┐
│ [城市切換: 台北 ▼]  最後更新：14:32                   │
├────────────────────────┬─────────────────────────────┤
│                        │  選定景點名稱               │
│   Mapbox 地圖          │  ┌─────────────────┐        │
│   - 景點燈號圓點        │  │  GaugeChart     │        │
│     🟢🟡🔴           │  │  即時人潮 73%   │        │
│   - 點擊 → 右側更新     │  └─────────────────┘        │
│                        │                             │
│                        │  TimelineChart              │
│                        │  過去 24 小時趨勢            │
│                        │                             │
│                        │  AI 建議                    │
│                        │  「建議改往...」              │
└────────────────────────┴─────────────────────────────┘
│  排行榜：[西門町 🔴] [信義區 🔴] [大安公園 🟡] ...    │
└──────────────────────────────────────────────────────┘
```

---

#### 組件 4：AED 急救地圖

```
┌──────────────────────────────────────────────────────┐
│ [城市切換: 台北 ▼] [場所類型: 全部 ▼]                │
├────────────────────────┬─────────────────────────────┤
│                        │  DistrictChart              │
│   Mapbox 地圖          │  各區每萬人 AED 數           │
│   - AED 點位           │  （色階圖）                  │
│   - 500m 覆蓋圓         │                             │
│   - 點擊 → 詳情         │  KPI 卡片（TextUnit）       │
│                        │  總台數 / 覆蓋率 / 最缺區    │
│                        │                             │
│                        │  AI 洞察                    │
│                        │  「缺口最大的區域是...」      │
└────────────────────────┴─────────────────────────────┘
```

---

#### 組件 5：急診即時壅塞度

```
┌──────────────────────────────────────────────────────┐
│ [城市切換: 台北 ▼]  最後更新：14:35                   │
├─────────────────────────┬────────────────────────────┤
│                         │  選定醫院名稱              │
│   Mapbox 地圖           │  ┌────────────────┐        │
│   - 醫院燈號            │  │ GaugeChart     │        │
│     🟢🟡🔴⚫          │  │ 壅塞度 78%     │        │
│                         │  └────────────────┘        │
│                         │                            │
│                         │  HeatmapChart              │
│                         │  一週 × 24hr 壅塞熱力圖    │
│                         │                            │
│                         │  AI 分流建議               │
│                         │  「建議考慮...」            │
└─────────────────────────┴────────────────────────────┘
```

---

#### 組件 10：AI 決策卡片（副作用視覺化）

```
┌──────────────────────────────────────────────────────┐
│ ⚠️ 災害警示：淡水河水位 7.5m（>警戒 7.3m）           │
│ [劇本：強颱+淹水 ▼]                                  │
├────────────────────────┬─────────────────────────────┤
│                        │  決策卡片列（可捲動）        │
│   Mapbox 地圖          │                             │
│   - 即時：淹水範圍      │  ┌─────────────────────┐   │
│   - hover 決策卡時：    │  │🔴 高優先：關閉中正橋 │   │
│     橙色副作用圖層      │  │ 依據：水位+壅塞預測  │   │
│     綠色疏散路線        │  │ 效果：疏散+23%      │   │
│                        │  │⚠️副作用：忠孝橋+40%│   │
│                        │  │信心：0.82           │   │
│                        │  │[採納][延後][替代]   │   │
│                        │  └─────────────────────┘   │
│                        │                             │
│                        │  ┌─────────────────────┐   │
│                        │  │🟡 中：預防性疏散萬華 │   │
│                        │  │ ...                 │   │
│                        │  └─────────────────────┘   │
└────────────────────────┴─────────────────────────────┘
│  30秒摘要（AI）：「淡水河超警戒，建議立即...」         │
└──────────────────────────────────────────────────────┘
```

**副作用視覺化交互（關鍵）**：
- Hover 第一張卡 → 地圖橙色高亮忠孝橋路段
- Hover 第二張卡 → 地圖高亮萬華疏散路線
- 點擊「採納」→ 卡片變為已執行狀態（深色邊框）
- 點擊「替代」→ 展開替代方案卡片

---

### 共用設計規範

**每個組件必須有的元素**：
- 右上角：城市切換下拉（台北 / 雙北）
- 右上角：最後資料更新時間
- 底部或側邊：AI 洞察面板（可收合）
- 所有圖表移除後，地圖仍完整可用

**Apexcharts 圖表對應**：

| 用途 | 圖表類型 | Apexcharts 設定 |
|------|---------|----------------|
| 即時人潮 / 壅塞度 | GaugeChart | `type: 'radialBar'` |
| 24hr 趨勢 | TimelineChart | `type: 'line'` |
| 各區排行 | ColumnChart | `type: 'bar'` |
| 雙城對比 | 雙色 ColumnChart | `type: 'bar', stacked: false` |
| 設施密度 | DistrictChart | Mapbox choropleth（非 Apexcharts） |
| 一週壅塞熱力圖 | HeatmapChart | `type: 'heatmap'` |
| KPI 數字 | TextUnit | 純 HTML/CSS，非圖表 |
| 雷達圖 | RadarChart | `type: 'radar'` |

---

## 任務 C：AI Tool Calling 架構

**目標**：設計 Go 後端的 tool registry，讓 TWCC llama3.3-ffm-70b 能夠呼叫正確工具。

**技術限制**：
- LLM：只能用 `llama3.3-ffm-70b-16k-chat`（TWCC 大會指定）
- 代理伺服器：前端不得直接暴露 API Key，必須透過 Go 後端 Proxy
- Timeout：60s，Max Retry：2
- RPM 限制：30 RPM（每分鐘最多 30 次請求）

### Tool Registry 架構

```go
// tools/registry.go
package tools

type Tool struct {
    Name        string
    Description string
    InputSchema map[string]interface{}
    Handler     func(input map[string]interface{}) (string, error)
}

var Registry = []Tool{
    SummarizeEventsTool,
    AnalyzeCrowdTool,
    CompareCulturalDensityTool,
    AnalyzeAEDCoverageTool,
    AnalyzeERStatusTool,
    AnalyzeFoodSafetyTool,
    CompareScenariosTool,
    AnalyzeShelterGapTool,
    AnalyzeFloodRiskTool,
    AssessSituationTool,
    GenerateDecisionsTool,
    VisualizeSideEffectsTool,
    GenerateBriefingTool,
}
```

### 關鍵 Tool 規格

#### `generate_decisions`（組件 10 核心）

```go
// tools/generate_decisions.go
var GenerateDecisionsTool = Tool{
    Name: "generate_decisions",
    Description: "根據當前災害情況，生成優先級排序的決策建議清單，每個建議包含依據、預期效果和副作用",
    InputSchema: map[string]interface{}{
        "type": "object",
        "properties": map[string]interface{}{
            "scenario_id": map[string]interface{}{
                "type":        "string",
                "description": "劇本 ID，例如 tw-typhoon-flood-001",
            },
            "current_sensors": map[string]interface{}{
                "type":        "object",
                "description": "當前感測器資料快照（水位、雨量、道路狀況）",
            },
        },
        "required": []string{"scenario_id"},
    },
    Handler: func(input map[string]interface{}) (string, error) {
        // 1. 從 DB 查詢劇本定義
        // 2. 整合即時感測器資料
        // 3. 比對歷史相似案例（NCDR）
        // 4. 返回結構化決策清單 JSON
    },
}
```

**輸出格式**：

```json
{
  "decisions": [
    {
      "id": "d001",
      "priority": "critical",
      "action": "關閉中正橋雙向車道",
      "evidence": [
        { "source": "CWA 水位 API", "value": "淡水河 7.5m > 警戒 7.3m" },
        { "source": "MATSim 預跑 001", "value": "中正橋壅塞預測 95%" }
      ],
      "expected_effect": "疏散效率提升 23%",
      "side_effects": [
        {
          "description": "忠孝橋負荷增加 40%",
          "severity": "medium",
          "map_highlight": {
            "type": "road_segment",
            "coordinates": [[121.4987, 25.0478], [121.5012, 25.0501]],
            "color": "#FF8C00"
          }
        }
      ],
      "confidence": 0.82,
      "source_trace": ["CWA-E73305A4-20260415-1432", "MATSIM-001-PRERUN"]
    }
  ]
}
```

#### `visualize_side_effects`（副作用視覺化）

```go
var VisualizeSideEffectsTool = Tool{
    Name: "visualize_side_effects",
    Description: "將決策的副作用轉為 Mapbox 地圖圖層規格，供前端即時高亮",
    InputSchema: map[string]interface{}{
        "type": "object",
        "properties": map[string]interface{}{
            "decision_id": map[string]interface{}{
                "type": "string",
            },
        },
    },
    Handler: func(input map[string]interface{}) (string, error) {
        // 返回 Mapbox Layer Spec JSON
        // 前端直接用 map.addLayer() 套用
    },
}
```

**輸出格式（Mapbox Layer Spec）**：

```json
{
  "layers": [
    {
      "id": "side-effect-congestion",
      "type": "line",
      "source": {
        "type": "geojson",
        "data": {
          "type": "FeatureCollection",
          "features": [
            {
              "type": "Feature",
              "geometry": {
                "type": "LineString",
                "coordinates": [[121.4987, 25.0478], [121.5012, 25.0501]]
              },
              "properties": {
                "severity": "medium",
                "description": "忠孝橋負荷增加 40%"
              }
            }
          ]
        }
      },
      "paint": {
        "line-color": "#FF8C00",
        "line-width": 4,
        "line-opacity": 0.8
      }
    }
  ]
}
```

### API 路由設計

```
POST /api/ai/chat
  Body: { message: string, context: { component_id, city, current_data } }
  → 呼叫 TWCC LLM + Tool Calling
  → 返回 AI 回應 + 觸發的 tool 結果

GET  /api/ai/decisions?scenario_id=001
  → 直接返回決策清單（不走 LLM，查表）

GET  /api/ai/side-effects?decision_id=d001
  → 返回 Mapbox Layer Spec

POST /api/ai/briefing
  Body: { scenario_id, city }
  → 生成 30 秒指揮官摘要
```

### TWCC Proxy 實作

```go
// services/twcc_proxy.go
type TWCCProxy struct {
    apiURL   string // TWCC_API_URL
    apiKey   string // TWCC_API_KEY
    model    string // llama3.3-ffm-70b-16k-chat
    timeout  int    // 60s
    maxRetry int    // 2
}

func (p *TWCCProxy) Chat(messages []Message, tools []Tool) (*Response, error) {
    // 1. 建立 request（帶 tool definitions）
    // 2. 送往 TWCC API
    // 3. 若回應含 tool_calls → 執行 tool handler → 繼續對話
    // 4. 返回最終文字回應
    // 5. 失敗時 retry（最多 2 次）
}
```

### RPM 限流策略

由於限制 30 RPM，需要：

```go
// middleware/rate_limiter.go
// 使用 Redis 計數器（比賽技術棧已包含 Redis）
// 超過 30 RPM 時：
// - 返回快取的最後一次 AI 回應（標記為 "cached"）
// - 或排隊等待（若等待 < 5 秒）
// - 避免 Demo 時因 RPM 超標造成 AI 無回應
```

---

## 優先執行順序

```
Phase 0（現在）：規劃完成 ✅

Phase 1（賽前 2 週）：
  [ ] 完成資料源驗證清單（任務 A）
  [ ] 確認景點人潮燈號 API 是否公開
  [ ] 確認急診即時資訊 API 格式

Phase 2（賽前 1 週）：
  [ ] 完成所有 10 個組件的 wireframe 細節（任務 B）
  [ ] 建立 Tool Registry 骨架（任務 C）
  [ ] 建立 Mock Data Generator（給燈號 Demo 用）

Phase 3（黑客松當天 0-4h）：
  [ ] 鎖定 5 個劇本 JSON Schema
  [ ] 確認前端版型（哪個組件先上）
  [ ] 分工：前端 / 後端 / 資料工程 / AI Tool

Phase 4（黑客松 4-48h）：
  [ ] 依 13-component-specs.md 開發組件
  [ ] 優先完成地圖組件（評審最看重）
  [ ] 最後完成決策卡片副作用視覺化（★ 殺手鐧）
```

---

## 尚未完成的事項（待辦）

- [ ] **資料源驗證**：逐一打 API，填入驗證結果表（任務 A 結果欄）
- [ ] **景點人潮燈號**：找到正確的 API endpoint（可能需要問台北市府）
- [ ] **Wireframe 細節**：組件 3/6/7/8 的 layout 待補完
- [ ] **MATSim 預跑**：5 個劇本需要賽前跑完靜態結果
- [ ] **MiroFish GraphRAG**：種子資料需要人工收集（颱風歷史新聞）
- [ ] **分工表**：依團隊人數分配任務
- [ ] **Demo 腳本細節**：14-demo-script.md 待撰

---

*最後更新：2026-04-15*
