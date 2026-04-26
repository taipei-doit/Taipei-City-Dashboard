---
name: page
description: 當使用者要建立新頁面（View）、新增路由、或建立包含組件與地圖的獨立頁面時觸發此技能。關鍵字：新頁面、新 View、addRoute、新增路由、page、頁面
---

# 建立新頁面

建立新頁面是一個多步驟任務。請依照以下順序執行，並在每個步驟確認相關規範。

## 開始前

向使用者確認以下資訊（如尚未提供）：

1. **頁面名稱與路由路徑**（例：`Dispatch1999View`、`/dispatch-1999`）
2. **Layout 類型**：
   - 左側組件 + 右側地圖（同 MapView）
   - 純組件 grid（同 DashboardView）
   - 其他自定義 layout
3. **資料來源**：使用既有 contentStore dashboard 流程，或自行呼叫 API
4. **組件清單**：每個組件的圖表類型、是否有地圖
5. **額外功能**：城市切換、收藏、定時更新、彈跳視窗等
6. **視覺對標**：這個頁面要跟**哪個既有頁面**長得像？（MapView / DashboardView / 其他？）
   **必答**，讓 Step 0 知道要讀哪個檔案。

## Step 0：觀摩既有實作（MANDATORY，不可跳過）

寫任何一行新 Vue 之前，**必須**讀使用者在 Q6 指定的對標頁面，並讀以下檔案（依頁面類型）：

| 頁面類型 | Step 0 必讀 |
|---|---|
| 含地圖（MapView 式）| `src/views/MapView.vue`、`src/components/map/MapContainer.vue`、`src/store/mapStore.js` 的 `initializeMapBox` / `addMapLayer` |
| 純組件 grid（DashboardView 式）| `src/views/DashboardView.vue`、`src/dashboardComponent/DashboardComponent.vue` props 清單 |
| 有圖表 | 一個既有 `src/dashboardComponent/components/*.vue`（對應 Q4 的圖表類型） |

讀完後，**在對話中回報以下對照**（不可省略）：

- 既有頁面的 UI 骨架（SideBar / SettingsBar / 卡片殼 / 地圖殼分別是哪些元件）
- 你打算**重用**哪些、**自幹**哪些
- 任何**明確偏離既有樣式**的點（例：「不用 DashboardComponent 殼，自己寫卡片 → 視覺會有差」）

使用者確認對照表後，才進 Step 1。

### Step 0.5：盤點 `src/components/utilities/` 與 `src/components/dialogs/`（**MANDATORY**）

開工前**必須**先掃過 `Taipei-City-Dashboard-FE/src/components/utilities/` 與 `src/components/dialogs/` 兩個資料夾，列清楚現有的工具元件清單──這是這個專案累積的視覺／互動共用資產，**不得自己生成已存在的元件**。常見會撞名重做的：

- `utilities/bars/`（NavBar / SideBar / SettingsBar / AdminSideBar / ComponentSideBar）
- `utilities/miscellaneous/`（SideBarTab / MobileLayerTab 等）
- `utilities/forms/`、`utilities/buttons/`、`utilities/loading/` 等通用 input / button / loading
- `dialogs/`（MoreInfo / ReportIssue / FindClosestPoint / NotificationBar / LogIn 等彈窗）

判定流程：
1. **能直接用**：用 import 路徑帶進新 view，不要拷貝樣式或重寫
2. **需要小改但符合精神**：先在對話中說明你要怎麼擴 props / slot，待使用者同意，再改原元件（而非另開一個）
3. **真的不適用**才允許自幹──但要在對話中明確列出「`utilities/X` 為什麼不適用」，避免之後 review 才發現可以重用

**反模式**：看到要做 link / button / sidebar 條目就直接寫 inline `<a>` 或新元件，沒先去 `utilities/` 看──這條會讓 demo 視覺與主站脫節，且重複的 CSS 散落各處難維護。

### 重用優先原則

- **預設**：重用既有殼與子組件
  - **頁面殼**：`NavBar`（含 tab 列）、`SideBar`、`SettingsBar`──不要在 view 裡自己刻第二條 tab；用 `meta.layout === "dashboard"` 與 NavBar 的 `tabContext` 機制（見步驟二）
  - **內容元件**：`DashboardComponent`、`MapContainer`、`dashboardComponent/components/*`、`ComponentTag`、`dialogStore`、`mapStore`
  - **工具元件**：`src/components/utilities/**`、`src/components/dialogs/**` 的所有既有元件（見上方 Step 0.5 強制盤點）
- **Opt-out 條件**：使用者明示「獨立 demo 頁」「不要用共用元件」才自幹
- 即使 opt-out，CSS 變數（`--color-*`、`--font-*`）與 `rules/code-style.md` 的命名／順序規則**仍強制遵守**

## 步驟一：建立 View 元件

在 `src/views/` 下建立 Vue 元件。

- 命名規則：參照 .claude/rules/code-style.md 的「Vue 元件」段落
- 程式碼結構：參照 .claude/rules/code-style.md 的「Vue 元件」結構順序
- 樣式規範：參照 .claude/rules/uiux.md 的系統顏色與間距變量
- 詳細示範：參照 .claude/skills/page/reference/page-creation-guide.md

### 含地圖的頁面必備元素

- 引入 `MapContainer` 元件
- 引入 `mapStore`，處理 toggle / filter / fly 事件
- 用 `computed` 將組件分為 hasMap / noMap 兩組
- 實作 `handleToggle()`、`shouldDisable()` 函式

### 純組件 grid 頁面必備元素

- 使用 CSS grid 排版，參照 DashboardView.vue 的 media query 斷點
- 不需要引入 MapContainer 和 mapStore

## 步驟二：註冊路由

在 `src/router/index.js` 的 `routes` 陣列新增路由定義。

### **重要｜預設掛 dashboard 殼（NavBar + SideBar + SettingsBar）**

新路由 **預設要加 `meta: { layout: "dashboard" }`**，App.vue 看到這個 meta 就會把該路由套上跟 `/dashboard` `/mapview` 一樣的殼（NavBar 在頂、SideBar 在左、SettingsBar 在內容上方）。

```js
{
    path: "/<your-route>",
    name: "<your-route>",
    component: YourView,
    meta: { layout: "dashboard" },   // ← 預設加這行
}
```

**只有 embed／全螢幕展示／登入 callback 等特殊頁才省略此 meta**，落到 App.vue 的 `<router-view />` fallback 分支（無殼）。

### 切 tab 用既有 NavBar，不要在 view 裡自己刻 tab 列

`NavBar.vue` 已經有「儀表板總覽 / 地圖交叉比對」兩個 tab。如果你的頁面也是「圖表 / 地圖」雙模式，**不要自己在 view 裡再寫一條 tab 列**。做法：

1. 註冊兩個路由 `/<your-route>` 與 `/<your-route>/mapview`，都指向同一個 View（或拆兩個 View 也可）
2. 在 `NavBar.vue` 的 `tabContext` computed 裡加判斷：當 `route.path.startsWith('/<your-route>')` 時，把兩個 tab 連結指向自己的 dashboard / mapview 路徑
3. View 裡用 `route.name` 或 `route.path` 切 `v-if` 渲染對應內容

範例：[`src/views/AccessibilityRouteView.vue`](../../../Taipei-City-Dashboard-FE/src/views/AccessibilityRouteView.vue) + [`src/components/utilities/bars/NavBar.vue` 的 `tabContext`](../../../Taipei-City-Dashboard-FE/src/components/utilities/bars/NavBar.vue)。

## 步驟三：SideBar 加分頁 link（**強制**）

每個新頁面都必須在 SideBar 加一條入口──**沒有 link 等於使用者找不到頁面**，視覺上也會有「設了路由但側欄沒進入點」的破口。即使你只是要做個 demo / 一次性展示，仍要加；用完移除一條 link 比留個遺孤路由乾淨。

### 加在哪

`src/components/utilities/bars/SideBar.vue` 內，依新頁面性質：

| 頁面性質 | 放法 |
|---|---|
| **示範 / demo / prototype** | 在「公共儀表板」h1 之前加「示範儀表板」section（若已存在則直接加 link） |
| **正式儀表板**（會走 contentStore dashboard 流程）| 由 BE 注入到 `contentStore.cityManager` / 公共儀表板清單，SideBar 自動產生（不必手寫 link）|
| **管理 / 工具頁** | 視情況加在側欄底部、配對應 icon |

### Demo 頁的 link 範本

```vue
<!-- 在「公共儀表板」h1 之前 -->
<h1>{{ isExpanded ? `示範儀表板` : `示範` }}</h1>
<RouterLink
    :to="$route.path.startsWith('/<your-route>') ? $route.path : '/<your-route>'"
    class="sidebar-demo-link"
    active-class="sidebar-demo-link-active"
>
    <span :title="!isExpanded ? '<你的頁面標題>' : ''"><material-icon-name></span>
    <h3 v-if="isExpanded"><你的頁面標題></h3>
</RouterLink>
```

`to` 用三元式的原因：使用者已經在你的 mapview tab 時，點側欄 link 不該被踢回 dashboard tab──保留當前 sub-route。

### 樣式（首次加 demo link 時建立，之後共用）

`SideBar.vue` 已有 `.sidebar-demo-link` 與 `.sidebar-demo-link-active` 兩個 class（仿 SideBarTab 視覺）。新增時直接套用即可，**不要自己另寫一套樣式**。

## 步驟四：設定路由守衛

在 `src/router/index.js` 中修改對應的 `router.beforeEach`：

- 內容載入守衛（約第 164 行）：加入新路由的資料載入邏輯
  - 自訂 `meta.layout === "dashboard"` 路由的 `currentDashboard` 由 view 自管（在 view onMounted 寫 `contentStore.currentDashboard.name = "..."` 給 SettingsBar 顯示），守衛已自動跳過 `clearCurrentDashboard()`
- 地圖清除守衛：含地圖的頁面不應清除 mapStore；`meta.layout === "dashboard"` 路由也已自動轉成 `clearOnlyLayers()`
- 行動裝置守衛：決定新頁面是否允許行動裝置存取
- 權限守衛：決定新頁面是否需要登入

## 步驟五：（通常不用動）App.vue layout

App.vue 已根據 `route.meta?.layout === "dashboard"` 自動套用 NavBar + SideBar + SettingsBar 殼。**只有當你需要新的 layout（非 dashboard、非 admin、非 component）時才動 App.vue**，這種情況請先在 `docs/` 寫架構決議。

## 步驟六：加入圖表組件

如果頁面包含圖表：
- 圖表資料格式：讀取 .claude/skills/chart/reference/chart-data.md
- 圖表類型與設定：讀取 .claude/skills/chart/reference/chart-type.md
- 圖表元件結構：讀取 .claude/skills/chart/SKILL.md

## 步驟七：加入地圖圖層

如果頁面包含地圖：
- 地圖資料格式：讀取 .claude/skills/map/reference/map-data.md
- 地圖類型與設定：讀取 .claude/skills/map/reference/map-type.md
- 地圖篩選功能：讀取 .claude/skills/map/reference/map-filter.md
- 底圖與圖層基礎：讀取 .claude/skills/map/SKILL.md

## 步驟八：加入彈跳視窗（如需要）

如果頁面需要彈跳視窗：
- 讀取 .claude/skills/dialog/SKILL.md
- 在 dialogStore 註冊新彈跳視窗
- 彈跳視窗 Vue 元件放在觸發元素旁邊，不要重複放置

## 完成後檢查

- [ ] Vue 元件命名為 PascalCase 且至少兩個英文字
- [ ] CSS root class 與元件名一致（全小寫無空格）
- [ ] CSS 屬性順序符合 code-style.md
- [ ] 使用專案定義的 CSS 變量（--color-*、--font-*）
- [ ] 路由有 `meta.layout: "dashboard"`（除非確定要用 fallback layout）
- [ ] **SideBar 已加新頁面 link**（demo 頁加在「示範儀表板」section；找不到 link 等於頁面不存在）
- [ ] NavBar `tabContext` 已更新（若新頁面有 dashboard / mapview 雙 tab）
- [ ] 路由守衛正確處理資料載入與地圖清除（`meta.layout` 已自動處理；除非有特殊需求）
- [ ] 不產生 console.log（ESLint no-console 規則）
- [ ] 執行 `npm run lint` 確認無錯誤
