# Project Overview — Taipei City Dashboard

> 給 Claude Code 的專案速讀。讀這份 + 每個子 skill 的 SKILL.md 就能開工。

## 專案使命

臺北城市儀表板（Taipei City Dashboard）是由 Taipei Urban Intelligence Center (TUIC) 開發的資料視覺化平台，整合臺北／新北雙北的開放資料，讓政策制定者與市民都能探索城市數據。

- 2.0 版為公開平台，原始碼開源
- 官方網站：`citydashboard.taipei`
- 文件：`citydashboard.taipei/documentation/`

## Monorepo 結構（工作邊界！）

```
Taipei-City-Dashboard/
├── Taipei-City-Dashboard-FE/    ← 前端（Vue 3）← **協作者只動這裡**
├── Taipei-City-Dashboard-BE/    ← 後端（Go）       不要動
├── Taipei-City-Dashboard-DE/    ← 資料工程        不要動
├── db-sample-data/              ← 範例資料        不要動
├── docker/                      ← 容器配置        不要動
├── helm-chart/                  ← K8s 部署        不要動
├── docs/                        ← Claude 輸出目錄
└── .claude/                     ← Claude Code 設定
```

**若必須跨專案改動**：先在 `docs/` 寫架構決議並告知使用者，不要直接動 BE / DE / docker / helm。

## FE 技術棧（以 `Taipei-City-Dashboard-FE/package.json` 為真相依據）

### dependencies

| 類別 | 套件（版本同 package.json）|
|---|---|
| Framework | `vue ^3.4.15` + Composition API（`<script setup>`）|
| State | `pinia ^2.1.7` |
| Routing | `vue-router ^4.2.5` |
| Charts | `apexcharts ^3.45.2` + `vue3-apexcharts ^1.4.4` |
| Maps | `mapbox-gl ^3.1.0` + `@deck.gl/core ^9.0.9` + `@deck.gl/layers ^9.0.9` + `@deck.gl/mapbox ^9.0.9` + `three ^0.163.0` + `threebox-plugin ^2.2.7` |
| Icons | `material-icons ^1.13.12`（另在 `index.html` 以 Google Fonts CDN 載入 Material Icons Round，兩者並存）|
| HTTP | `axios ^1.6.5` |
| Date | `dayjs ^1.11.10` |
| Utils | `@vueuse/core ^10.7.2`、`@turf/turf ^6.5.0`、`lodash.debounce ^4.0.8`、`uuid ^9.0.1` |
| Streaming | `hls.js ^1.6.7`（HLS 影音串流）|

### devDependencies

| 類別 | 套件 |
|---|---|
| Build | `vite ^5.0.12` + `@vitejs/plugin-vue ^5.0.3` + `vite-plugin-compression ^0.5.1` |
| Styling preprocessor | `sass ^1.70.0`（SCSS）|
| Linting | `@eslint/js ^9.0.0` + `eslint-plugin-vue ^9.20.1`（flat config：`eslint.config.js`）|

### package.json 裡沒有 ⇒ 視為專案不使用

- ❌ **Prettier**（無 `prettier` 依賴、無 `.prettierrc` 檔）
- ❌ **TypeScript**（`main.js` 非 `.ts`，無 `typescript` 依賴）
- ❌ **TailwindCSS** 或任何 CSS 框架
- ❌ 任何 UI component 庫（Material UI、Element Plus、Vuetify、Ant Design 等）
- ❌ 任何測試框架（vitest / jest / playwright / cypress）
- ❌ i18n 套件（vue-i18n 等）
- ❌ 表單驗證庫（vee-validate、zod 等）

### ⚠️ 與 rules 的既存不一致

`.claude/rules/code-style.md` 首段寫「本專案使用 Prettier 進行程式自動編排」，並提及配置檔 `.eslintrc.json` 與 `.prettierrc`──但 package.json 無 prettier 依賴，且兩個配置檔都不存在（實際是 `eslint.config.js`）。

**以 package.json 為真相**：本專案**不使用 Prettier**。若未來要導入，需先 `npm install -D prettier` 並建立 `.prettierrc`。rules 文字建議後續另案修正。

## FE 目錄結構

```
Taipei-City-Dashboard-FE/
├── index.html
├── package.json
├── vite.config.js
├── eslint.config.js
├── public/
└── src/
    ├── App.vue
    ├── main.js                    ← 全域元件註冊點（圖表、指令、apexcharts）
    ├── router/
    │   ├── index.js               ← 路由定義 + 守衛（資料載入／地圖清除／行動裝置／權限）
    │   └── axios.js               ← axios instance + interceptor
    ├── store/                     ← Pinia stores
    │   ├── contentStore.js        ← 儀表板內容／組件資料／API 呼叫
    │   ├── mapStore.js            ← Mapbox 物件、圖層、篩選、fly
    │   ├── dialogStore.js         ← 全域彈跳視窗狀態
    │   ├── authStore.js           ← 登入／權限
    │   ├── adminStore.js          ← 後台管理
    │   └── chatStore.js           ← 聊天（AI 輔助功能）
    ├── views/                     ← 頁面層（路由目標）
    │   ├── DashboardView.vue      ← 純組件 grid 頁面
    │   ├── MapView.vue            ← 左組件 + 右地圖
    │   ├── ComponentView.vue      ← 單組件檢視
    │   ├── ComponentInfoView.vue
    │   ├── EmbedView.vue          ← 嵌入式
    │   ├── CallBack.vue           ← OAuth callback
    │   └── admin/                 ← 後台頁面
    ├── components/                ← 共用 UI 元件（含 ComponentContainer、MapContainer 等基座）
    ├── dashboardComponent/        ← **儀表板內的圖表 Vue 元件**（chart skill 的目標）
    ├── directives/                ← 自定義 Vue directive
    └── assets/
        ├── configs/
        │   ├── apexcharts/        ← chartTypes.js（註冊圖表類型）
        │   └── mapbox/            ← mapConfig.js / mapStyle.js
        └── images/
```

## 兩種主要頁面類型

### DashboardView（純組件 grid）

- CSS grid 排版，RWD 斷點
- 不含地圖
- 依 `contentStore` 載入組件清單 → 呼叫 API → 每個組件渲染在 `ComponentContainer`

### MapView（左組件 + 右地圖）

- 引入 `MapContainer` 元件與 `mapStore`
- 組件分 `hasMap` / `noMap` 兩組（用 `computed`）
- 組件支援 toggle（控制地圖圖層開關）、filter（控制圖表篩選回寫地圖）、fly（地圖飛行）
- 地圖初始化：`mapStore.initializeMapBox()` → `initializeBasicLayers()`（行政區、里界、3D 建物）

## 資料流

```
1. 路由 beforeEach 觸發資料載入守衛
2. contentStore 呼叫 BE API 取得組件清單 + 每個組件的統計資料
3. 資料填入組件 config 的 chart_data 參數
4. ComponentContainer 渲染對應圖表 Vue 元件（依 chart_config.types）
5. 圖表元件收四個 props：activeChart / chart_config / series / map_config（+ 選擇性 map_filter）
6. 地圖頁面：mapStore 依 map_config 加圖層、處理篩選、fly 到中心點
```

詳細資料格式見：
- `.claude/skills/chart/reference/chart-data.md`
- `.claude/skills/chart/reference/chart-type.md`
- `.claude/skills/map/reference/map-data.md`
- `.claude/skills/map/reference/map-type.md`
- `.claude/skills/map/reference/map-filter.md`

## 設計哲學（節錄自 rules/uiux.md）

- **簡約**：只用最能代表資料集的關鍵圖表類型；視覺化細節放在彈跳視窗，不直接塞入儀表板
- **明確命名**：組件名包含資料來源／時間間隔／統計方法（例「信令人口分時統計」優於「人潮變化」）
- **風格一致**：CSS variables 統一顏色（`--color-background` `#090909`、`--color-highlight` `#5a9cf8` 等），字體層級 `--font-l/m/s`
- **相容性**：臺北市行政區順序固定、圖表間可互換

## 技術決策速記

| 問題 | 決策 |
|---|---|
| 為什麼不用 TypeScript？| 沿用 2.0 JavaScript 實作，保持新協作者入門門檻低 |
| 為什麼不用 TailwindCSS？| 全域 + 局部 SCSS 已足夠，保留客製空間 |
| 為什麼沒有測試框架？| 尚未建立；若要新增需先在 `docs/` 提架構決議 |
| 為什麼有 deck.gl + threebox + Mapbox？| deck.gl 做 WebGL 圖層（熱力、3D 柱狀）、threebox 做 3D 模型疊圖、Mapbox 提供底圖與一般圖層 |
| 為什麼有 chatStore？| AI 輔助查詢功能（未在本次文件細論）|

## 相關連結

- 官方站：<https://citydashboard.taipei>
- 中文文件：<https://tuic.gov.taipei/documentation/front-end/introduction>
- License：見 `LICENSE`
- GitHub：<https://github.com/tpe-doit/Taipei-City-Dashboard>
