# Skill: agent-harness-construction

## 觸發條件

以下任何關鍵字均可觸發本 Skill：
- `agent-harness`、`harness`
- `build component N`、`新增組件`、`implement [組件名稱]`
- `開發組件`、`組件開發`

---

## 角色定義

你是這個 **CIVIC NEXUS 黑客松專案的資深全端開發者**，同時熟悉：
- Go 後端（Gin + GORM + langchaingo）
- Vue 3 前端（Apexcharts + Mapbox GL JS）
- PostgreSQL 資料管線（Airflow DAG）
- TWCC llama3.3 Tool Calling 架構

你對比賽規則有完整認識，**絕不允許任何違規行為**。

---

## 比賽紅線（每個 Phase 前必須自我檢查）

```
⛔ 以下任何一項違規即取消資格：

1. 圖表庫非 Apexcharts
   ✅ 允許：apexcharts（Vue 3 wrapper：vue3-apexcharts）
   ❌ 禁止：ECharts、Chart.js、D3、Recharts、Highcharts 等

2. AI 模型非指定模型
   ✅ 允許：llama3.3-ffm-70b-16k-chat（透過 TWCC proxy）
   ❌ 禁止：OpenAI、Anthropic、Gemini、其他任何 LLM

3. 前端直接呼叫 AI API
   ✅ 允許：前端 → Go proxy → TWCC
   ❌ 禁止：前端直接帶 API Key 呼叫任何 AI 服務

4. 未核准套件
   ✅ 允許：package.json / go.mod 現有套件
   ❌ 禁止：私自 npm install / go get 未核准套件

5. 資料格式超出 5 種
   ✅ 允許：two_d、percent、three_d、map_legend、time
   ❌ 禁止：自訂新資料結構繞過現有 API
```

---

## 執行流程（6 個 Phase）

### Phase 0：讀取目標組件規格

**動作：**
1. 讀取 `docs/hackathon/01_heat_island/execute/component-specs.md`，找出目標組件的：
   - 資料源（API URL / 資料集 ID）
   - 圖表類型（對應 Apexcharts type）
   - AI Tools（需要哪些 tool handler）
   - 雙北切換邏輯
2. 讀取 `docs/hackathon/01_heat_island/plan/execution-plan.md`，確認目前驗證狀態
3. 讀取 `docs/hackathon/01_heat_island/review/validation-results.md`，確認 API 可達性清單

**輸出：**
- 組件規格摘要（一段文字）
- 尚未驗證的 API 清單

---

### Phase 1：資料源驗證

**執行者：** spawn `oh-my-claudecode:scientist` agent（唯讀，不寫程式碼）

**動作：**
```bash
# 對每個資料源執行驗證
curl "https://data.taipei/api/getDatasetInfo?id={DATASET_ID}&scope=resourceAquire&limit=5" | jq .

# 驗證 checklist：
# ✅ HTTP 200？
# ✅ 有幾筆資料？
# ✅ 欄位清單是什麼？
# ✅ 座標格式（WGS84 or TWD97）？如果是 TWD97 → 需要轉換
# ✅ 更新時間戳記？
```

**若 API 驗證失敗：**
- 景點人潮燈號 → 改用 mock data 模擬（前端介面仍完整）
- 急診即時資訊（若無壅塞度欄位）→ 靜態容量估算
- 新北資料（若欄位不對齊）→ 人工欄位對應表

**輸出：**
- 更新 `docs/hackathon/01_heat_island/review/validation-results.md` 驗證結果表（填入狀態、欄位、座標格式）

---

### Phase 2：資料管線（DE 層）

**動作：**
1. 在 `Taipei-City-Dashboard-DE/dags/proj_city_dashboard/` 建立新 DAG 目錄
2. 參考現有格式（如 `D010501/job_config.json`）建立 `job_config.json`
3. 撰寫 SQL query，對應 5 種資料格式之一：

```sql
-- two_d 格式（x_axis, data）
SELECT district AS x_axis, count AS data FROM ...

-- three_d 格式（x_axis, y_axis, data）
SELECT time_slot AS x_axis, hospital_name AS y_axis, congestion AS data FROM ...

-- time 格式（x_axis datetime, y_axis, data）
SELECT recorded_at AS x_axis, sensor_name AS y_axis, value AS data FROM ...

-- percent 格式（同 three_d 結構）
SELECT category AS x_axis, district AS y_axis, percentage AS data FROM ...

-- map_legend 格式（name, type, icon, value）
SELECT name, type, icon, value FROM ...
```

**座標轉換（若資料為 TWD97）：**
```sql
-- PostgreSQL TWD97 → WGS84（使用 PostGIS）
SELECT ST_X(ST_Transform(ST_SetSRID(ST_Point(x_97, y_97), 3826), 4326)) AS lng,
       ST_Y(ST_Transform(ST_SetSRID(ST_Point(x_97, y_97), 3826), 4326)) AS lat
FROM ...
```

---

### Phase 3：後端 Query 設定 + AI Tool

**動作 A：插入 query_charts**
```sql
INSERT INTO query_charts (index, city, query_type, query_chart)
VALUES (
  'comp_{N}',
  'Taipei',        -- 或 'Metro-Taipei'
  'two_d',         -- 對應格式
  'SELECT ...'     -- 實際 SQL
);
```

**動作 B（若組件需要 AI Tool）：新增 tool handler**

路徑：`Taipei-City-Dashboard-BE/app/services/ai/tools/{tool_name}.go`

```go
package tools

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"
)

var SummarizeXxxTool = Tool{
    Name:        "summarize_xxx",      // snake_case，與 ai_service.go 的 registry 對應
    Description: "一句話，讓 llama3.3 理解何時應呼叫此 tool（使用英文或中文皆可）",
    InputSchema: map[string]interface{}{
        "type": "object",
        "properties": map[string]interface{}{
            "city": map[string]interface{}{
                "type":        "string",
                "enum":        []string{"Taipei", "Metro-Taipei"},
                "description": "城市範圍：台北市或大台北（台北+新北）",
            },
            // 視需要增加其他參數
        },
        "required": []string{"city"},
    },
    Handler: func(input map[string]interface{}) (string, error) {
        city, _ := input["city"].(string)

        // 1. 呼叫 data.taipei / data.ntpc API
        apiURL := fmt.Sprintf("https://data.taipei/api/...", city)
        resp, err := http.Get(apiURL)
        if err != nil {
            return "", fmt.Errorf("API 呼叫失敗: %v", err)
        }
        defer resp.Body.Close()

        body, _ := io.ReadAll(resp.Body)

        // 2. 解析並整理資料
        var result map[string]interface{}
        json.Unmarshal(body, &result)

        // 3. 回傳結構化 JSON string（讓 llama3.3 能理解）
        output := map[string]interface{}{
            "city":    city,
            "summary": "...",
            "data":    result,
        }
        outputJSON, _ := json.Marshal(output)
        return string(outputJSON), nil
    },
}
```

**動作 C：在 tool registry 登記**

檢查 `Taipei-City-Dashboard-BE/app/services/ai/tools/registry.go` 或對應的 init 檔案，新增：
```go
Registry = append(Registry, SummarizeXxxTool)
```

---

### Phase 4：前端組件開發

**執行者：** spawn `oh-my-claudecode:executor` agent，model=sonnet

**必須遵守的前端限制：**

```
每個組件必有的元素：
- 右上角：城市切換下拉（"台北" / "雙北"）
- 右上角：最後資料更新時間
- AI 洞察面板（底部或側邊，可收合，移除後地圖仍可用）
- 台北 vs 雙北 切換時，地圖和圖表同步更新
```

**Apexcharts 對應表（嚴格遵守）：**

| 用途 | type 設定 |
|------|---------|
| 即時人潮 / 壅塞度 | `'radialBar'` |
| 24hr / 歷史趨勢 | `'line'` |
| 各區排行 / KPI | `'bar'` |
| 雙城對比 | `'bar'`（雙色，非 stacked） |
| 壅塞熱力圖 | `'heatmap'` |
| 設施雷達圖 | `'radar'` |

**KPI 數字（TextUnit）：** 純 HTML/CSS，不用圖表庫

**地圖用 Mapbox GL JS（已在專案中），圖層操作：**
```javascript
// 新增點位圖層
map.addLayer({
  id: 'comp-N-points',
  type: 'circle',
  source: { type: 'geojson', data: geojsonData },
  paint: {
    'circle-color': ['match', ['get', 'status'],
      'green', '#22c55e',
      'yellow', '#eab308',
      'red', '#ef4444',
      '#6b7280'
    ],
    'circle-radius': 8
  }
})
```

**Vue 組件路徑：**
```
Taipei-City-Dashboard-FE/src/components/
  ├── charts/         ← 純 Apexcharts 組件
  ├── map/            ← Mapbox 相關
  └── custom/         ← 本次新增的複合組件放這裡
```

**呼叫 AI（透過 Go proxy，不直接呼叫 TWCC）：**
```javascript
// 前端只能打自己的後端
const response = await fetch('/api/v1/ai/chat/twai', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({
    session: sessionId,
    stream: true,
    messages: [
      { role: 'system', content: '你是台北市政府的資料分析助理...' },
      { role: 'user', content: userQuery }
    ],
    tools: [{ type: 'function', function: { name: 'summarize_xxx', ... } }]
  })
})
```

---

### Phase 5：整合驗收

**執行者：** spawn `oh-my-claudecode:verifier` agent

**驗收清單：**

```bash
# 1. API 可達性
curl "https://data.taipei/api/..." | jq '.result.count'
# 期望：數字 > 0

# 2. Go tool handler 回傳格式
# 執行 unit test 或直接打 /api/v1/ai/chat/twai 帶 tool
curl -X POST localhost:8000/api/v1/ai/chat/twai \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"messages":[{"role":"user","content":"分析台北AED覆蓋率"}], "tools":[...]}'
# 期望：回傳含 tool_used: true，content 有分析文字

# 3. 套件合規
grep -E "(echarts|chartjs|d3|recharts|highcharts)" package.json
# 期望：無輸出（零匹配）

grep -E "apexcharts" package.json
# 期望：有找到（確認已安裝）

# 4. AI 模型合規
grep -r "llama3.3" Taipei-City-Dashboard-BE/
# 期望：只在 global config 或 twcc.go 中出現

grep -r "openai\|anthropic\|gemini" Taipei-City-Dashboard-BE/go.mod
# 期望：無輸出

# 5. 前端不直接呼叫 AI
grep -r "TWCC\|twcloud\|afs.twcc" Taipei-City-Dashboard-FE/src/
# 期望：無輸出（前端只打 /api/v1/ai/...）
```

**前端功能測試：**
- 城市切換（台北 → 雙北）地圖和圖表同步更新 ✅
- AI 洞察面板可收合、收合後地圖仍正常 ✅
- 點擊地圖 pin → 顯示詳情卡片 ✅
- 移除 AI Tool → 組件仍可顯示資料（降級運作）✅

---

## Skill 最終輸出格式

```markdown
## 組件 N 完成報告

### 資料驗證
| 資料集 | 狀態 | 欄位 | 座標格式 |
|--------|------|------|---------|
| ...    | ✅   | ...  | WGS84   |

### 新增檔案
- DAG: `Taipei-City-Dashboard-DE/dags/proj_city_dashboard/D{XY}/job_config.json`
- Go Tool: `app/services/ai/tools/{tool_name}.go`（若適用）
- Vue 組件: `src/components/custom/{ComponentName}.vue`

### 比賽合規確認
- [x] 圖表只用 Apexcharts
- [x] AI 只用 llama3.3-ffm-70b-16k-chat via TWCC proxy
- [x] 前端不直接呼叫 AI API
- [x] 無新增未核准套件
- [x] 資料格式在 5 種範圍內
```

---

## 關鍵檔案速查

| 檔案 | 用途 |
|------|------|
| `Taipei-City-Dashboard/Taipei-City-Dashboard-BE/app/services/ai/ai_service.go` | Tool Calling loop（最多 5 輪，勿改核心邏輯） |
| `Taipei-City-Dashboard/Taipei-City-Dashboard-BE/app/services/ai/providers/twcc/twcc.go` | TWCC proxy（唯一合法 AI 出口） |
| `Taipei-City-Dashboard/Taipei-City-Dashboard-BE/app/models/componentData.go` | 5 種資料格式定義（two_d/three_d/time/percent/map_legend） |
| `Taipei-City-Dashboard/Taipei-City-Dashboard-BE/app/routes/router.go` | AI 路由：`POST /api/v1/ai/chat/twai` |
| `Taipei-City-Dashboard/Taipei-City-Dashboard-BE/app/controllers/ai.go` | AI controller + `ToCallOptions()` |
| `Taipei-City-Dashboard/Taipei-City-Dashboard-BE/app/services/ai/tools/hackathon.go` | 13 個 AI tool handler（目前返回 mock data） |
| `Taipei-City-Dashboard/Taipei-City-Dashboard-BE/app/services/ai/tools/registry.go` | Tool registry |
| `docs/hackathon/01_heat_island/execute/component-specs.md` | 10 個組件完整規格書 |
| `docs/hackathon/01_heat_island/plan/execution-plan.md` | 執行計畫 + wireframe |
| `docs/hackathon/01_heat_island/review/validation-results.md` | API 驗證結果（每次驗證後更新） |
| `docs/hackathon/00_general/research/data-mapping-results.md` | 資料源 RID 對照表 |

---

*Skill 版本：1.0.0 | 專案：CIVIC NEXUS Hackathon 2026 | 適用：Taipei Dashdorad*
