# 🏙️ Taipei City Dashboard — 前端 (FE)

> **Taipei City Dashboard** 是由臺北市政府資訊局（TUIC）開發的開放原始碼城市資料視覺化平台。  
> 本文件針對 `Taipei-City-Dashboard-FE` 前端專案，說明技術架構、套件規範，以及如何新增儀表板組件。

---

## 📖 目錄

1. [技術堆疊概覽](#技術堆疊概覽)
2. [目錄結構](#目錄結構)
3. [環境設定與啟動](#環境設定與啟動)
4. [套件清單與規範](#套件清單與規範)
5. [路由架構](#路由架構)
6. [狀態管理（Pinia Stores）](#狀態管理pinia-stores)
7. [視圖（Views）](#視圖views)
8. [元件架構](#元件架構)
9. [圖表組件總覽](#圖表組件總覽)
10. [ComponentConfig 資料結構](#componentconfig-資料結構)
11. [新增儀表板組件指南](#新增儀表板組件指南)
12. [全域樣式與設計規範](#全域樣式與設計規範)
13. [開發工具與規範](#開發工具與規範)

---

## 技術堆疊概覽

| 類別 | 技術 |
|------|------|
| 框架 | Vue 3 (Composition API + `<script setup>`) |
| 建置工具 | Vite 5 |
| 狀態管理 | Pinia 2 |
| 路由 | Vue Router 4 |
| 圖表庫 | ApexCharts（`vue3-apexcharts`）|
| 地圖渲染 | Mapbox GL JS 3、deck.gl 9 |
| 3D 地圖 | three.js + threebox-plugin |
| 地理運算 | @turf/turf |
| HTTP 請求 | Axios |
| 時間工具 | Day.js |
| 圖示 | Material Icons Round |
| CSS 預處理器 | SCSS（Sass）|
| 工具函數 | VueUse、lodash.debounce、uuid |

---

## 目錄結構

```
Taipei-City-Dashboard-FE/
├── public/                   # 靜態資源（不經過 Vite 處理）
├── src/
│   ├── assets/
│   │   ├── configs/          # 圖示清單 (AllIcons.js)、時間映射 (AllTimes.js)
│   │   │   ├── apexcharts/   # ApexCharts 預設設定檔
│   │   │   └── mapbox/       # Mapbox 地圖樣式設定檔
│   │   ├── styles/
│   │   │   ├── globalStyles.css   # 全域 CSS 變數與重置樣式
│   │   │   ├── chartStyles.css    # ApexCharts tooltip 樣式覆寫
│   │   │   └── toggleswitch.css   # 開關元件樣式
│   │   └── utilityFunctions/ # 共用工具函數（時間框架計算等）
│   ├── components/
│   │   ├── charts/           # 歷史圖表（HistoryChart.vue）
│   │   ├── dialogs/          # 彈窗元件（登入、設定、下載等）
│   │   ├── icons/            # 圖示元件
│   │   └── utilities/
│   │       ├── bars/         # 導覽列（NavBar、SideBar、SettingsBar 等）
│   │       ├── forms/        # 表單元件（CheckBox、InputTags 等）
│   │       └── miscellaneous/ # 雜項元件（ComponentTag、SideBarTab 等）
│   ├── dashboardComponent/   # 📦 核心儀表板組件庫（可獨立發布）
│   │   ├── DashboardComponent.vue  # 主容器元件
│   │   ├── components/       # 所有圖表類型元件（23 種）
│   │   ├── assets/           # 圖表預覽 SVG
│   │   ├── styles/           # 組件庫專屬樣式
│   │   └── utilities/        # 組件庫工具（型別定義、城市管理等）
│   ├── directives/           # 自訂 Vue 指令（horizontalWheel）
│   ├── router/
│   │   ├── index.js          # Vue Router 路由定義與導航守衛
│   │   └── axios.js          # Axios 實例（含攔截器）
│   ├── store/                # Pinia 狀態管理
│   │   ├── contentStore.js   # 儀表板資料與組件資料
│   │   ├── mapStore.js       # 地圖狀態（圖層、濾鏡、視角）
│   │   ├── authStore.js      # 使用者認證
│   │   ├── dialogStore.js    # 彈窗顯示控制
│   │   ├── adminStore.js     # 後台管理資料
│   │   └── chatStore.js      # AI 聊天室
│   ├── views/                # 頁面視圖
│   │   ├── DashboardView.vue
│   │   ├── MapView.vue
│   │   ├── ComponentView.vue
│   │   ├── ComponentInfoView.vue
│   │   ├── EmbedView.vue
│   │   ├── CallBack.vue
│   │   └── admin/            # 後台管理頁（User、Dashboard、Issue 等）
│   ├── App.vue               # 根元件
│   └── main.js               # Vue 應用程式進入點
├── .env                      # 環境變數（不納入版控）
├── .env.template             # 環境變數範本
├── eslint.config.js          # ESLint 設定
├── .prettierrc               # Prettier 格式化設定
├── vite.config.js            # Vite 建置設定
└── package.json
```

---

## 環境設定與啟動

### 1. 複製環境變數

```bash
cp .env.template .env
```

填入 `.env` 所需變數：

| 變數名稱 | 說明 |
|----------|------|
| `VITE_API_URL` | 後端 API 基礎路徑（預設 `/api/dev`）|
| `VITE_MAPBOXTOKEN` | Mapbox GL 存取金鑰（必填，地圖才能渲染）|
| `VITE_MAPBOXTILE` | Mapbox 自訂地圖樣式 URL |
| `VITE_TAIPEIPASS_URL` | TaipeiPass OAuth URL（外部開發者不需填）|
| `VITE_TAIPEIPASS_CLIENT_ID` | TaipeiPass OAuth Client ID |
| `VITE_TAIPEIPASS_SCOPE` | TaipeiPass OAuth Scope |

### 2. 安裝套件

```bash
npm install
```

### 3. 啟動開發伺服器

```bash
npm run dev
# 或
npm start
```

> 預設監聽於 `http://localhost:80`（可透過 vite.config.js 調整）

### 4. 建置生產版本

```bash
npm run build        # 正式環境
npm run build:test   # 測試環境
```

### 5. 預覽建置結果

```bash
npm run preview
```

---

## 套件清單與規範

> ⚠️ **規範：新增儀表板組件時，只能使用下方已列出的套件。若有新需求，請先提出討論。** 擅自引入新套件可能造成 bundle 過大或版本衝突。

### Production Dependencies（核心依賴）

| 套件 | 版本 | 用途 | 使用場景 |
|------|------|------|----------|
| `vue` | ^3.4 | 前端框架 | 所有元件 |
| `vue-router` | ^4.2 | 前端路由 | `src/router/` |
| `pinia` | ^2.1 | 狀態管理 | `src/store/` |
| `axios` | ^1.6 | HTTP 請求 | `src/router/axios.js`，透過 `http` 實例使用 |
| `vue3-apexcharts` | ^1.4 | 圖表渲染（ApexCharts Vue 封裝）| 圖表組件中用 `<apexchart>` |
| `apexcharts` | ^3.45 | ApexCharts 核心 | 搭配 vue3-apexcharts |
| `mapbox-gl` | ^3.1 | 地圖渲染引擎 | `mapStore.js`、地圖相關視圖 |
| `@deck.gl/core` | ^9.0 | WebGL 地圖圖層引擎 | 地圖 deck.gl 圖層 |
| `@deck.gl/layers` | ^9.0 | deck.gl 標準圖層 | 地圖點/線/面圖層 |
| `@deck.gl/mapbox` | ^9.0 | deck.gl + Mapbox 整合 | mapStore 地圖渲染 |
| `three` | ^0.163 | 3D 渲染引擎 | 3D 地圖物件（threebox）|
| `threebox-plugin` | ^2.2 | Mapbox 上的 3D 物件 | 3D 建築、車輛動畫 |
| `@turf/turf` | ^6.5 | 地理空間運算 | GeoJSON 處理、距離計算 |
| `dayjs` | ^1.11 | 日期/時間格式化 | 資料時間框架計算 |
| `@vueuse/core` | ^10.7 | Vue 組合式工具函數 | `useEventListener`、`useResizeObserver` 等 |
| `lodash.debounce` | ^4.0 | 函數防抖 | Pinia 動作的 debounce |
| `uuid` | ^9.0 | 唯一 ID 生成 | 地圖視角等唯一識別 |
| `hls.js` | ^1.6 | HLS 影片串流 | 串流影像播放組件 |
| `material-icons` | ^1.13 | Material Icons 字型 | 所有圖示 `<span>icon_name</span>` |

### DevDependencies（開發工具）

| 套件 | 用途 |
|------|------|
| `vite` | 建置工具與開發伺服器 |
| `@vitejs/plugin-vue` | Vite 的 Vue SFC 支援 |
| `sass` | SCSS 預處理器（在 `<style lang="scss">` 中使用）|
| `vite-plugin-compression` | 建置時 gzip 壓縮產出 |
| `eslint-plugin-vue` | Vue SFC ESLint 規則 |
| `@eslint/js` | ESLint 核心 JS 規則 |

### ❌ 禁止引入的套件類型

- **UI 元件庫**（Element Plus、Naive UI、Vuetify 等）— 本專案使用自訂設計系統
- **CSS 框架**（TailwindCSS、Bootstrap 等）— 專案使用純 SCSS
- **替代圖表庫**（ECharts、Chart.js 等）— 統一使用 ApexCharts
- **替代地圖庫**（Leaflet、OpenLayers 等）— 統一使用 Mapbox GL + deck.gl
- **替代日期庫**（moment.js、date-fns 等）— 統一使用 Day.js

---

## 路由架構

所有路由定義於 `src/router/index.js`，並設有多層導航守衛：

| 路由路徑 | 名稱 | 說明 |
|----------|------|------|
| `/dashboard` | `dashboard` | 主儀表板頁 |
| `/mapview` | `mapview` | 地圖視圖頁 |
| `/component` | `component` | 組件管理頁（需登入）|
| `/component/:index` | `component-info` | 組件詳情頁 |
| `/embed/:id/:city` | `embed` | 嵌入單一組件用 |
| `/admin/dashboard` | `admin-dashboard` | 後台儀表板管理（需管理員）|
| `/admin/user` | `admin-user` | 後台使用者管理 |
| `/admin/contributor` | `admin-contributor` | 後台貢獻者管理 |
| `/admin/edit-component` | `admin-edit-component` | 後台組件編輯 |
| `/admin/issue` | `admin-issue` | 後台問題回報管理 |
| `/admin/disaster` | `admin-disaster` | 後台災害管理 |

**導航守衛邏輯（按順序執行）：**
1. 設定 `authStore.currentPath`
2. 行動裝置窄視窗重導向（僅允許 dashboard、component-info、embed、mapview）
3. 未登入者無法進入需認證的路由
4. 依路由觸發 `contentStore` 與 `mapStore` 的資料載入

---

## 狀態管理（Pinia Stores）

| Store | 檔案 | 主要職責 |
|-------|------|----------|
| `contentStore` | `contentStore.js` | 儀表板列表、組件資料、圖表資料的 API 載入與快取 |
| `mapStore` | `mapStore.js` | Mapbox 地圖實例、圖層管理、GeoJSON 濾鏡、視角操控 |
| `authStore` | `authStore.js` | 使用者 Token、登入狀態、裝置偵測（行動/窄視窗）|
| `dialogStore` | `dialogStore.js` | 控制各彈窗的顯示/隱藏狀態 |
| `adminStore` | `adminStore.js` | 後台管理頁的資料（使用者、組件、問題等）|
| `chatStore` | `chatStore.js` | AI 聊天室的訊息狀態 |

### 在組件中使用 Store

```js
import { useContentStore } from "@/store/contentStore";

const contentStore = useContentStore();
// 讀取資料
const components = contentStore.currentDashboard.components;
```

---

## 視圖（Views）

| 視圖 | 說明 |
|------|------|
| `DashboardView.vue` | 格狀排列儀表板組件，支援拖曳排序 |
| `MapView.vue` | 左側圖表 + 右側 Mapbox 地圖的分割視圖 |
| `ComponentView.vue` | 組件瀏覽與自定義儀表板管理 |
| `ComponentInfoView.vue` | 單一組件的詳細資訊頁 |
| `EmbedView.vue` | 可嵌入外部網站的單一組件視圖 |
| `CallBack.vue` | TaipeiPass OAuth 回調頁 |

---

## 元件架構

### Utility 層（`src/components/utilities/`）

| 元件 | 說明 |
|------|------|
| `bars/NavBar.vue` | 上方導覽列（路由連結、使用者選單）|
| `bars/SideBar.vue` | 左側儀表板列表側邊欄 |
| `bars/ComponentSideBar.vue` | 組件管理側邊欄 |
| `bars/SettingsBar.vue` | 設定面板 |
| `bars/AdminSideBar.vue` | 後台管理側邊欄 |
| `forms/CustomCheckBox.vue` | 自訂 checkbox |
| `forms/InputTags.vue` | 標籤輸入框 |
| `forms/SelectButtons.vue` | 按鈕組選擇器 |
| `forms/TableHeader.vue` | 可排序的表頭 |
| `miscellaneous/ComponentTag.vue` | 小型標籤（顯示地圖/歷史資料功能提示）|
| `miscellaneous/SideBarTab.vue` | 側邊欄分頁 Tab |

### Dialog 層（`src/components/dialogs/`）

| 彈窗 | 說明 |
|------|------|
| `AddComponent.vue` | 新增組件至儀表板 |
| `AddEditDashboards.vue` | 新增/編輯儀表板 |
| `LogIn.vue` | 登入對話框 |
| `DownloadData.vue` | 資料下載 |
| `MoreInfo.vue` | 組件詳細資訊 |
| `ChatBox.vue` | AI 聊天室 |
| `ReportIssue.vue` | 回報問題 |
| `UserSettings.vue` | 使用者設定 |
| `EmbedComponent.vue` | 嵌入連結產生器 |

---

## 圖表組件總覽

所有圖表組件位於 `src/dashboardComponent/components/`，透過 `DashboardComponent.vue` 的 `returnChartComponent()` 方法動態渲染。

| 組件名稱（英文 key）| 中文名稱 | 說明 |
|--------------------|----------|------|
| `BarChart` | 橫向長條圖 | 水平長條，適合分類比較 |
| `ColumnChart` | 縱向長條圖 | 垂直長條，適合時序資料 |
| `BarPercentChart` | 長條圖(%) | 長條圖百分比堆疊 |
| `BarChartWithGoal` | 長條圖(目標) | 含目標線的長條圖 |
| `DonutChart` | 圓餅圖 | 環狀圓餅，適合比例展示 |
| `TreemapChart` | 矩形圖 | 面積比例示意 |
| `DistrictChart` | 行政區圖 | 台北各行政區著色地圖 |
| `MetroChart` | 捷運行駛圖 | 台北捷運路線圖 |
| `TimelineSeparateChart` | 折線圖(比較) | 多系列折線，各自獨立 |
| `TimelineStackedChart` | 折線圖(堆疊) | 多系列折線堆疊 |
| `GuageChart` | 量表圖 | 半圓儀表板 |
| `SpeedometerChart` | 儀表板圖 | 全圓儀表（目前保留未用）|
| `RadarChart` | 雷達圖 | 多維度雷達 |
| `HeatmapChart` | 熱力圖 | 矩陣熱力分布 |
| `PolarAreaChart` | 極座標圖 | 極坐標面積圖 |
| `ColumnLineChart` | 長條折線圖 | 長條 + 折線複合 |
| `IconPercentChart` | 圖示比例圖 | 以圖示數量表示比例 |
| `IndicatorChart` | 指標圖 | 單一數值指標卡 |
| `TextUnitChart` | 文字數值圖 | 純文字數值顯示 |
| `MapLegend` | 地圖圖例 | 地圖顏色/符號說明 |

> **新增圖表類型時，需同步更新：**
> 1. `src/dashboardComponent/components/` — 新增 Vue 組件
> 2. `src/dashboardComponent/utilities/chartTypes.ts` — 新增 key/中文名稱對應
> 3. `src/dashboardComponent/DashboardComponent.vue` 的 `returnChartComponent()` — 新增 case
> 4. `src/dashboardComponent/assets/chart/` — 新增預覽 SVG 圖

---

## ComponentConfig 資料結構

每個儀表板組件的設定由後端 API 回傳，遵循以下 TypeScript 型別定義（`utilities/componentConfig.ts`）：

```typescript
type ComponentConfig = {
  id: number;              // 組件唯一 ID
  index: string;           // 組件識別字串（英文、用於 API 路徑）
  name: string;            // 組件顯示名稱（中文）
  source: string;          // 資料來源說明
  time_from: string;       // 資料起始時間（"static" | "current" | "demo" | "maintain" | 時間字串）
  time_to: string;         // 資料結束時間（"now" 或日期字串）
  update_freq: number | null;        // 更新頻率數值
  update_freq_unit: string | null;   // 更新頻率單位（"day" | "hour" | "month" 等）
  short_desc: string;      // 組件簡短描述
  chart_config: ChartConfig;
  chart_data: any;         // 由 API 動態填入
  map_config: MapConfig[] | null;
  map_filter: MapFilter | null;
  history_config: HistoryConfig | null;
};

type ChartConfig = {
  color: string[];         // 圖表顏色陣列（支援 hex）
  types: string[];         // 圖表類型陣列（可有多個，會顯示切換按鈕）
  unit: string | null;     // 數值單位（顯示於 Y 軸或 tooltip）
  categories: string[] | null; // X 軸分類標籤（可由 API 動態回傳）
};

type MapConfig = {
  index: string;           // 地圖圖層識別字串
  type: string;            // 圖層類型（"fill" | "circle" | "line" | "symbol" 等）
  paint: any;              // Mapbox paint 屬性
  property: any[];         // 圖層資料屬性定義
  title: string;           // 圖層顯示名稱
  size: string | null;     // 符號/圓圈大小
  icon: string | null;     // Mapbox 符號圖示名稱
  source: string;          // GeoJSON 資料來源 key
};

type MapFilter = {
  mode: string;            // "byParam" | "byLayer"
  byParam: {
    xParam: string;        // 篩選用的 X 參數欄位名稱
    yParam: string;        // 篩選用的 Y 參數欄位名稱
  } | null;
};

type HistoryConfig = {
  color: string[] | null;  // 歷史圖顏色（null 表示使用預設）
  range: string[];         // 歷史時間範圍陣列（e.g. ["day", "month", "year"]）
};
```

---

## 新增儀表板組件指南

### 方式一：使用現有圖表類型（最常見）

只需在後端 DB 新增組件設定，前端即可自動渲染。設定重點如下：

1. **決定圖表類型** — 從上方 [圖表組件總覽](#圖表組件總覽) 選擇一個或多個 `chart_config.types`
2. **設定 `chart_config.color`** — 提供足夠數量的顏色陣列
3. **確認 `time_from`** — 常用值：
   - `"static"` — 固定資料
   - `"current"` — 即時資料
   - `"demo"` — 示範靜態資料
   - `"1month"` / `"3month"` / `"1year"` — 動態時間範圍

4. **若需地圖圖層**，填寫 `map_config` 陣列，並準備對應的 GeoJSON 資料

### 方式二：新增全新圖表類型

若現有圖表類型無法滿足需求，請依照以下步驟：

#### Step 1：建立圖表組件

在 `src/dashboardComponent/components/` 建立新的 Vue SFC，例如 `MyNewChart.vue`。

組件需接受下列 Props（保持一致性）：

```vue
<script setup>
const props = defineProps({
  activeChart: { type: String, required: true },  // 當前啟用的圖表類型名稱
  activeCity: { type: String, default: "" },       // 城市篩選
  chart_config: { type: Object, required: true },  // ChartConfig 物件
  series: { type: Array, required: true },         // 圖表資料（chart_data）
  map_config: { type: Array, default: null },
  map_filter: { type: Object, default: null },
  map_filter_on: { type: Boolean, default: false },
});

const emits = defineEmits([
  "filterByParam",    // 地圖濾鏡（byParam 模式）
  "filterByLayer",    // 地圖濾鏡（byLayer 模式）
  "clearByParamFilter",
  "clearByLayerFilter",
  "fly",              // 地圖飛行至指定位置
]);
</script>
```

> 只顯示在 `activeChart === '你的組件名稱'` 時才渲染，以支援多圖表切換：
> ```vue
> <div v-if="activeChart === 'MyNewChart'">...</div>
> ```

#### Step 2：使用 ApexCharts 渲染圖表

```vue
<template>
  <div v-if="activeChart === 'MyNewChart'">
    <apexchart
      type="bar"
      :options="chartOptions"
      :series="chartSeries"
      height="100%"
    />
  </div>
</template>

<script setup>
import { computed } from "vue";

const chartOptions = computed(() => ({
  colors: props.chart_config.color,
  chart: { toolbar: { show: false }, background: "transparent" },
  theme: { mode: "dark" },
  // ... 其他 ApexCharts 設定
}));

const chartSeries = computed(() => {
  // 將 props.series 轉換為 ApexCharts 格式
  return props.series.map(item => ({ name: item.name, data: item.data }));
});
</script>
```

#### Step 3：在 `chartTypes.ts` 新增類型

```typescript
// src/dashboardComponent/utilities/chartTypes.ts
export const chartTypes: chartType = {
  // ... 現有類型 ...
  MyNewChart: "我的新圖表",   // 新增這行
};
```

#### Step 4：在 `DashboardComponent.vue` 註冊

```js
// 1. import 組件
import MyNewChart from "./components/MyNewChart.vue";
import MyNewChartSvg from "./assets/chart/MyNewChart.svg";

// 2. 在 returnChartComponent() 的 switch 中新增 case
case "MyNewChart":
  return svg ? MyNewChartSvg : MyNewChart;
```

#### Step 5：製作預覽 SVG

在 `src/dashboardComponent/assets/chart/` 放置 `MyNewChart.svg`，  
這個 SVG 會在組件預覽模式（`mode="preview"`）中顯示。

---

## 全域樣式與設計規範

### CSS 設計變數（`globalStyles.css`）

所有組件應優先使用這些 CSS 變數，保持設計一致性：

```css
/* 顏色 */
--color-background: #090909;           /* 頁面背景 */
--color-component-background: #282a2c; /* 組件卡片背景 */
--color-border: #494b4e;               /* 邊框顏色 */
--color-highlight: #5a9cf8;            /* 主要強調色（藍色）*/
--color-normal-text: white;            /* 主要文字顏色 */
--color-complement-text: #888787;      /* 次要文字顏色（灰色）*/
--color-overlay: rgba(0,0,0,0.65);    /* 遮罩層 */
--color-taipei: #1411AC;               /* 台北市品牌色 */
--color-metrotaipei: #ac7811;          /* 台北捷運品牌色 */

/* 字體大小 */
--font-xl: 1.5rem;
--font-l: 1.25rem;
--font-m: 18px;
--font-ms: 1rem;
--font-s: 0.75rem;

/* 圖示字型 */
--font-icon: "Material Icons Round";
--font-to-icon: 1.2;                   /* 圖示放大倍數（相對於 --font-l）*/
```

### 圖示使用方式

本專案使用 **Material Icons Round** 字型，以 `<span>` 元素顯示：

```html
<!-- 使用圖示 -->
<span>star</span>
<span>map</span>
<span>delete</span>
<span>settings</span>
```

> 所有可用圖示名稱請參考 [Material Icons](https://fonts.google.com/icons?icon.style=Rounded)

### 響應式斷點

| 類別 | 說明 |
|------|------|
| `hide-if-mobile` | 螢幕寬度 < 1000px 時隱藏 |
| `show-if-mobile` | 螢幕寬度 ≥ 1000px 時隱藏（僅行動版顯示）|

### SCSS 命名慣例

本專案使用 BEM-like 的方式命名 CSS class：

```scss
// 組件根元素
.dashboardcomponent { ... }

// 子元素用 - 連接
.dashboardcomponent-header { ... }
.dashboardcomponent-chart { ... }
.dashboardcomponent-footer { ... }

// 修飾符用 is/has 前綴
.isfavorite { ... }
.isDelete { ... }
```

---

## 開發工具與規範

### ESLint

使用 `eslint-plugin-vue` 搭配 `@eslint/js`：

```bash
npm run lint       # 自動修正 lint 問題
```

建置時會自動執行 lint：
```bash
npm run build      # 包含 eslint --fix
```

### Prettier

格式化設定於 `.prettierrc`。建議安裝 VS Code 的 Prettier 套件，並設定存檔時自動格式化。

### Vite 代理設定（`vite.config.js`）

開發時 API 代理：

| 路徑前綴 | 代理目標 |
|----------|----------|
| `/api` | `https://citydashboard.taipei/api/v1` |
| `/geo_server` | `https://citydashboard.taipei/geo_server/` |
| `/api/dev`（Docker）| `http://dashboard-be:8080` |

### 建置最佳化

- **Code Splitting**：每個 `node_modules` 套件自動分割為獨立 chunk
- **Gzip 壓縮**：`vite-plugin-compression` 自動壓縮產出
- **Chunk 警告上限**：1600 KB

---

## 快速參考

### 新增組件 Checklist

- [ ] 確認使用現有圖表類型，或依指南新增新類型
- [ ] 組件 Props 符合 `ComponentConfig` 型別規範
- [ ] 使用 CSS 變數而非 hardcode 顏色值
- [ ] 圖示使用 `<span>material_icon_name</span>` 格式
- [ ] 在 `chartTypes.ts` 中新增對應的中文名稱
- [ ] 在 `DashboardComponent.vue` 的 `returnChartComponent()` 中新增 case
- [ ] 準備預覽用 SVG

### 常用 import 路徑

```js
// Pinia Stores
import { useContentStore } from "@/store/contentStore";
import { useMapStore } from "@/store/mapStore";
import { useAuthStore } from "@/store/authStore";
import { useDialogStore } from "@/store/dialogStore";

// 工具函數
import { getComponentDataTimeframe } from "@/assets/utilityFunctions/dataTimeframe";

// API
import http from "@/router/axios";  // Axios 實例，直接使用 http.get/post

// 時間工具
import dayjs from "dayjs";
```

---

> 📌 本文件由 Taipei Urban Intelligence Center (TUIC) 維護。
> 如有疑問，請提交 Issue 或參閱 [官方文件](https://tuic.gov.taipei/documentation)。
