# Skill: component-quick-validator

## 觸發條件

以下任何關鍵字均可觸發本 Skill：
- `quick-validate`、`qv`、`快速驗證`
- `validate component N`、`驗證組件 N`
- `組件可行性`、`preview component`

---

## 角色定義

你是 **CIVIC NEXUS 黑客松專案的組件快速驗證專家**。

你的任務是在 **零基礎設施** 條件下（不啟動 Docker、不跑 Go 後端、不碰 PostgreSQL），用最輕量的方式驗證一個前端組件的可行性。

**核心武器**：curl + 自包含 HTML 檔案 + Claude Preview MCP 瀏覽器

**時間目標**：每個組件驗證 < 5 分鐘

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

## 執行流程（4 個 Phase）

### Phase 0：讀取目標組件規格

**動作：**
1. 讀取 `docs/hackathon/01_heat_island/execute/component-specs.md`，找出目標組件的：
   - 資料源（API URL / 資料集名稱）
   - 圖表類型（對應 Apexcharts type）
   - 地圖圖層需求（有/無、點/面/線）
   - AI Tool schema（tool name + input/output）
   - 雙北切換邏輯（CT 值對應）
2. 讀取 `docs/hackathon/01_heat_island/review/validation-results.md`，確認已知的 API 狀態

**輸出：**
- 一段文字摘要：「組件 N：{名稱}，需要 {X} 個資料源，{Y} 種圖表，地圖={有/無}」

---

### Phase 1：資料可達性驗證（curl only）

**對每個資料源執行：**

```bash
# 1. HTTP 狀態碼
curl -s -o /dev/null -w "%{http_code}" "API_URL"

# 2. 前 2000 bytes 樣本
curl -s "API_URL" | head -c 2000
```

**驗證 checklist（每個資料源）：**
- ✅ HTTP status（200/301/403/404）
- ✅ 回應有資料（非空 JSON/CSV）
- ✅ 關鍵欄位存在（lat/lng、name、value 等）
- ✅ 座標格式（WGS84 直接可用 / TWD97 需轉換）
- ✅ 資料筆數 > 0
- ✅ 最近更新時間

**API endpoint 注意事項：**
- data.taipei 舊的 `getDatasetInfo` 已 404
- 優先用新路由：`https://data.taipei/api/v1/dataset/{ID}?scope=resourceAquire&limit=5`
- 若仍失敗，嘗試 CSV 下載：`https://data.taipei/api/dataset/{dataset-id}/resource/{resource-id}/download`
- 新北：`https://data.ntpc.gov.tw/api/datasets/{ID}/json?size=5`

**若 API 不可達：**
- 標記為 `mock fallback`
- 從 curl 結果或規格書中擷取 3-5 筆代表性樣本資料
- 在 Phase 2 的 HTML 中使用 mock data，並標註 `// DATA SOURCE: mock`

---

### Phase 2：產生自包含 HTML 預覽

**產生一個 HTML 檔案到 `/tmp/validate-component-{N}.html`**

HTML 必須包含：

**1. CDN 引用（零本地依賴）**
```html
<script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
<script src="https://api.mapbox.com/mapbox-gl-js/v3.1.0/mapbox-gl.js"></script>
<link href="https://api.mapbox.com/mapbox-gl-js/v3.1.0/mapbox-gl.css" rel="stylesheet" />
```

**2. 嵌入資料**
- 真實資料：Phase 1 curl 取得的樣本
- Mock 資料：API 不可達時使用
- 必須標註：`// DATA SOURCE: real | mock`

**3. 圖表區塊**
嚴格對應 component-specs 的圖表類型：

| 用途 | ApexCharts type |
|------|----------------|
| 即時人潮 / 壅塞度 | `'radialBar'` |
| 24hr / 歷史趨勢 | `'line'` |
| 各區排行 / KPI | `'bar'` |
| 雙城對比 | `'bar'`（雙色，非 stacked） |
| 壅塞熱力圖 | `'heatmap'` |
| 設施雷達圖 | `'radar'` |
| KPI 數字 | 純 HTML/CSS（TextUnit，不用圖表庫） |

深色主題色票：
```css
body { background: #1e1e1e; color: #ccc; font-family: 'Noto Sans TC', sans-serif; }
```

**4. 地圖區塊（若組件 map=true）**
```javascript
mapboxgl.accessToken = 'YOUR_MAPBOX_ACCESS_TOKEN';
const map = new mapboxgl.Map({
  container: 'map',
  style: 'mapbox://styles/mapbox/dark-v11',
  center: [121.536609, 25.044808],  // 台北市中心
  zoom: 12.5
});
```
- 根據規格加入 GeoJSON source + layer
- 點位用 `circle`、面域用 `fill`、路線用 `line`
- 顏色用規格書中的色標

**5. 佈局**
```
┌─────────────────────────────────┐
│ [台北 ▼]  組件 N：{名稱}  [更新: HH:MM] │
├──────────────┬──────────────────┤
│              │   圖表區（40%）    │
│  地圖（60%）  │                  │
│              ├──────────────────┤
│              │ AI 洞察面板       │
│              │ [收合 ▲]         │
└──────────────┴──────────────────┘
```

**6. 互動**
- 城市切換下拉：台北 / 雙北（切換時替換資料源）
- AI 面板收合按鈕：點擊隱藏/顯示，確認移除 AI 後地圖+圖表仍完整

---

### Phase 3：視覺驗證（Claude Preview MCP）

**步驟：**

1. `mcp__Claude_Preview__preview_start` — 開啟 HTML 檔案
2. `mcp__Claude_Preview__preview_screenshot` — 截圖
3. 評估截圖：
   - 圖表成功渲染（無空白區域、無 JS 錯誤）
   - 地圖正確載入（中心點正確、marker 可見）
   - 佈局符合 wireframe 比例
   - 深色主題下文字可讀
   - 城市切換下拉可見
   - AI 面板收合功能正常
4. 若有問題，修正 HTML 再截圖（最多 2 輪迭代）
5. `mcp__Claude_Preview__preview_eval` 確認：
   ```javascript
   document.querySelectorAll('.apexcharts-canvas').length > 0  // 圖表有載入
   ```

---

### Phase 4：合規檢查 + 輸出報告

**靜態合規檢查：**
```
[x/fail] 圖表庫：HTML 中只有 ApexCharts CDN（無 echarts/chartjs/d3/recharts/highcharts）
[x/fail] AI 路徑：HTML 中無直接 TWCC/afs.twcc URL（AI 只經 /api/v1/ai/chat/twai）
[x/fail] 資料格式：圖表資料符合 5 種格式之一（two_d/three_d/time/percent/map_legend）
[x/fail] 套件合規：只引用 apexcharts + mapbox-gl CDN
[x/fail] AI 可移除：收合 AI 面板後，地圖 + 圖表仍正常渲染
```

**報告輸出到：**
`docs/hackathon/01_heat_island/execute/validation-reports/component-{N}-quickval.md`

**報告格式：**

```markdown
# 組件 {N} 快速驗證報告

**日期**：YYYY-MM-DD
**狀態**：PASS / PARTIAL / FAIL
**耗時**：Xm Ys

## 資料可達性
| 資料源 | URL | HTTP | 筆數 | 關鍵欄位 | 座標格式 | 更新時間 | 狀態 |
|--------|-----|------|------|---------|---------|---------|------|
| ...    | ... | 200  | 47   | lat,lng | WGS84   | 04-15   | OK   |

## 視覺預覽
- 截圖：（內嵌或路徑）
- 圖表渲染：YES/NO
- 地圖渲染：YES/NO
- 佈局符合 wireframe：YES/NO
- 深色主題可讀：YES/NO

## 合規檢查
- [x] 只用 ApexCharts
- [x] 無直接 AI API 呼叫
- [x] 資料格式合規（two_d）
- [x] 無未核准套件
- [x] AI 可移除

## AI Tool Schema 審查
- Tool 名稱：{tool_name}
- Input schema 合理：YES/NO
- hackathon.go 中已有 handler：YES/NO（第 {N} 行）
- 輸出格式符合規格：YES/NO

## 阻礙項
- （列出任何會阻擋正式開發的問題）

## Ready for Harness?
YES / NO（附原因）
```

---

## 決策邊界

**用這個 Skill 當：**
- 想快速測試一個組件想法是否可行
- 想確認 API 資料能不能轉成 ApexCharts/Mapbox
- 想在不起 Docker 的情況下看到視覺效果
- 想在正式開發前做一次合規預檢

**不要用這個 Skill 當：**
- 準備寫正式 Vue 組件程式碼 → 改用 `agent-harness-construction`
- 需要資料庫整合或 DE 層 DAG → 改用 `agent-harness-construction`
- 需要測試 AI Tool Calling 真實回傳 → 需要 Go 後端

**銜接規則：**
快速驗證報告顯示 `Ready for Harness: YES` → 建議啟動 `agent-harness-construction` 開發同一組件

---

## 關鍵檔案速查

| 檔案 | 用途 |
|------|------|
| `docs/hackathon/01_heat_island/execute/component-specs.md` | 10 組件完整規格書 |
| `docs/hackathon/01_heat_island/plan/execution-plan.md` | 執行計畫 + wireframe |
| `docs/hackathon/01_heat_island/review/validation-results.md` | API 驗證結果 |
| `docs/hackathon/00_general/research/data-mapping-results.md` | 資料源 RID 註冊表 |
| `Taipei-City-Dashboard-BE/app/services/ai/tools/hackathon.go` | 現有 13 個 tool handler |
| `Taipei-City-Dashboard-BE/app/services/ai/tools/registry.go` | Tool registry 定義 |
| `Taipei-City-Dashboard-BE/app/models/componentData.go` | 5 種資料格式定義 |
| `Taipei-City-Dashboard-FE/src/components/charts/HistoryChart.vue` | 參考圖表組件 |
| `Taipei-City-Dashboard-FE/package.json` | 核准套件清單 |

---

*Skill 版本：1.0.0 | 專案：CIVIC NEXUS Hackathon 2026 | 適用：Taipei Dashdorad*
