---
name: senior-fe-engineer
description: Use this skill when writing, refactoring, reviewing, or adding Vue frontend code for Taipei City Dashboard, especially dashboard chart components, ApexCharts, Mapbox integration, Pinia stores, SCSS, mock data, or API stubs.
---

# Senior Frontend Engineering Skill

## Description
當使用者要求撰寫、重構前端程式碼，或新增儀表板組件時，啟動此技能。

## Professional Instructions

### 1. 職人級開發規範
- **組件實作**：一律使用 `<script setup>`，並將組件置於 `src/components/` 或 `src/dashboardComponent/components/`。
- **樣式優先級**：優先使用 `globalStyles.css` 定義的 CSS 變數（如 `--color-background`, `--color-highlight`）。
- **圖示規範**：統一使用 Material Icons Round，格式為 `<span>icon_name</span>`。

### 2. 儀表板組件新增 SOP (核心)
當被要求新增圖表組件時，你必須確保執行以下步驟：
- **Step 1**: 建立 Vue SFC，並定義符合 `ComponentConfig` 的 Props（activeChart, series, chart_config 等）。
- **Step 2**: 實作 ApexCharts 渲染，並在 `activeChart === '你的名稱'` 時才渲染。
- **Step 3**: 在 `chartTypes.ts` 註冊新的 key 與中文名稱。
- **Step 4**: 修改 `DashboardComponent.vue` 的 `returnChartComponent()`，加入對應的 case。

### 3. 狀態管理原則
- 任何地圖狀態異動應透過 `mapStore.js`。
- 儀表板資料與組件快取應透過 `contentStore.js`。
- 使用 `lodash.debounce` 處理高頻率觸發的 Action。

### 4. 輸出與交付要求
- **必須提供 Diff**：修改現有代碼時，嚴禁直接丟出整份檔案。你必須使用 Markdown 的 `diff` 語法標註新增 (`+`) 與刪除 (`-`) 的行。
- **上下文保留**：Diff 必須包含足夠的上下文（上下各 3 行），確保使用者能定位修改位置。
- **Artifacts 使用**：如果是建立全新檔案，請使用 Antigravity 的 Artifacts 視窗產出；如果是修改舊檔案，請在對話框內產出 Diff。

### 5. 模擬驅動開發與 API 預留規範 (Mock & API Stubbing)
當後端 API 尚未就緒時，你必須遵循以下開發模式，確保未來能無縫接軌：

- **定義 Mock Object**：在組件內部建立一個名為 `mockData` 的常數，其資料結構必須嚴格遵循 `ComponentConfig` 與 `series` 的格式。
- **建立資料切換邏輯**：使用一個 `isMock` 的 flag (通常設為 true)，並在資料讀取處使用三元運算子：
  `const displayData = isMock ? mockData : props.series;`
- **標準註記標籤**：在預留串接 API 的位置，必須加上 `// TODO: API_INTEGRATION_POINT` 與 `// API_STUB` 註解，並說明該處預期接收的參數型別。
- **Store 預留口**：若涉及全域資料，請在 `contentStore.js` 中新增對應的 Action 存根（Stub），內容先回傳 `Promise.resolve(mockData)`。

### 6. 地圖聯動與複合式視覺化規範 (Map-Chart Integration)
當任務涉及「地圖圖層」或「圖表與地圖聯動」時，必須執行以下操作：

- **同步配置**：確保組件同時具備 `chart_config`（統計圖）與 `map_config`（地圖圖層）的 Mock 資料。
- **實作 Emit 事件**：所有複合式組件必須預留以下事件，以便與 `mapStore.js` 通訊：
    - `filterByParam`：當點擊圖表長條/圓餅時，觸發地圖資料篩選。
    - `fly`：觸發地圖移動（飛行）至特定座標。
- **互動邏輯**：
    - 在圖表組件的 `@click` 事件中，主動調用 `emit("filterByParam", payload)`。
    - 模擬資料時，必須包含一組符合 `map_config` 的 GeoJSON 屬性欄位。

## Verification
- 完成代碼後，請對照 README 中的「新增組件 Checklist」進行自我檢查。

## Required Context Files
Before making frontend changes, read:
- `.agent/rules/coding-standards.md`
- `.agent/context/frontend-readme-summary.md`
- `.agent/context/data-schemas.md`
- `.agent/context/chart-inventory.md`

## Cross-tool Compatibility
This skill is intended to be duplicated in both:
- `.agents/skills/senior-fe-engineer/SKILL.md` for Codex
- `.agent/skills/senior-fe-engineer/SKILL.md` for Antigravity
