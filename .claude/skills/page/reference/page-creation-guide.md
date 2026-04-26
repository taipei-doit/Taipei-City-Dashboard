# 建立含多個組件與地圖的新頁面

本文件說明如何在 Taipei City Dashboard 前端專案中，建立一個包含多個 `DashboardComponent` 與對應地圖的新頁面，並提供逐步指引與示範程式碼。

## 前置知識

頁面的資料流架構如下：

```
Route Guard → contentStore 載入資料 → View 渲染組件列表 → DashboardComponent 容器 → 圖表元件 + 地圖互動
```

核心概念：
- **contentStore** 管理組件資料（chart_data、chart_config、map_config）
- **mapStore** 管理 Mapbox 地圖實例與圖層
- **DashboardComponent** 是通用組件容器，根據 config 自動選擇渲染對應的圖表類型
- 地圖圖層在使用者開啟 toggle 時才載入（lazy loading）

---

## 步驟

### 步驟一：建立 View 元件

在 `Taipei-City-Dashboard-FE/src/views/` 下建立新的 Vue 元件。

**示範：`src/views/MyCustomView.vue`**

```vue
<script setup>
import { ref, computed, onMounted } from "vue";
import DashboardComponent from "../dashboardComponent/DashboardComponent.vue";
import MapContainer from "../components/map/MapContainer.vue";
import { useContentStore } from "../store/contentStore";
import { useMapStore } from "../store/mapStore";
import { useDialogStore } from "../store/dialogStore";

const contentStore = useContentStore();
const mapStore = useMapStore();
const dialogStore = useDialogStore();

// 追蹤每個組件的地圖 toggle 狀態
const toggleOn = ref([]);

// 將組件分為有地圖 / 無地圖兩組（參考 MapView.vue 的做法）
const parseMapLayers = computed(() => {
  const hasMap = myComponents.value.filter((item) => item.map_config[0]);
  const noMap = myComponents.value.filter((item) => !item.map_config[0]);
  return { hasMap, noMap };
});

// 組件資料來源：可從 contentStore 取得，或自行呼叫 API
const myComponents = computed(() => {
  return contentStore.currentDashboard.components || [];
});

// 地圖 toggle 開關
function handleToggle(value, map_config, index) {
  toggleOn.value[index] = value;
  if (!map_config[0]) {
    if (value) {
      dialogStore.showNotification("info", "本組件沒有空間資料，不會渲染地圖");
    }
    return;
  }
  if (value) {
    mapStore.addToMapLayerList(map_config);
  } else {
    mapStore.clearByParamFilter(map_config);
    mapStore.turnOffMapLayerVisibility(map_config);
  }
}

// 判斷圖層是否正在載入中（用於 disable toggle）
function shouldDisable(map_config) {
  const allMapLayerIds = map_config.map(
    (el) => `${el.index}-${el.type}-${el.city}`
  );
  if (mapStore.isPreloading) return true;
  return mapStore.loadingLayers.some((el) => allMapLayerIds.includes(el));
}
</script>

<template>
  <div class="my-custom-page">
    <!-- 左側：組件列表 -->
    <div class="my-custom-page-charts">
      <DashboardComponent
        v-for="(item, idx) in parseMapLayers.hasMap"
        :key="`${item.index}-${item.city}`"
        :config="item"
        mode="map"
        :info-btn="true"
        :active-city="item.city"
        :toggle-disable="shouldDisable(item.map_config)"
        :toggle-on="toggleOn[idx]"
        @toggle="(value, map_config) => handleToggle(value, map_config, idx)"
        @filter-by-param="
          (map_filter, map_config, x, y) =>
            mapStore.filterByParam(map_filter, map_config, x, y)
        "
        @filter-by-layer="
          (map_config, layer) => mapStore.filterByLayer(map_config, layer)
        "
        @clear-by-param-filter="
          (map_config) => mapStore.clearByParamFilter(map_config)
        "
        @clear-by-layer-filter="
          (map_config) => mapStore.clearByLayerFilter(map_config)
        "
        @fly="(location) => mapStore.flyToLocation(location)"
        @info="(item) => dialogStore.showMoreInfo(item)"
      />

      <!-- 無地圖的組件 -->
      <h2 v-if="parseMapLayers.noMap?.length > 0">無空間資料組件</h2>
      <DashboardComponent
        v-for="item in parseMapLayers.noMap"
        :key="`nomap-${item.index}-${item.city}`"
        :config="item"
        mode="map"
        :info-btn="true"
        :active-city="item.city"
        @info="(item) => dialogStore.showMoreInfo(item)"
      />
    </div>

    <!-- 右側：地圖 -->
    <MapContainer />
  </div>
</template>

<style scoped lang="scss">
.my-custom-page {
  height: calc(100vh - 127px);
  height: calc(var(--vh) * 100 - 127px);
  display: flex;
  margin: var(--font-m);

  &-charts {
    width: 370px;
    max-height: 100%;
    display: grid;
    row-gap: var(--font-m);
    margin-right: var(--font-s);
    overflow-y: scroll;
  }
}
</style>
```

**關鍵 props 說明：**

| Prop | 用途 |
|------|------|
| `config` | 組件完整配置（含 chart_config、map_config、chart_data） |
| `mode` | 顯示模式：`"default"` / `"half"` / `"map"` / `"halfmap"` / `"preview"` |
| `toggle-on` | 控制地圖圖層是否顯示 |
| `toggle-disable` | 圖層載入中時禁用 toggle |

**關鍵 events 說明：**

| Event | 用途 |
|-------|------|
| `@toggle` | 使用者開關地圖圖層 |
| `@filter-by-param` | 點擊圖表資料點篩選地圖 |
| `@filter-by-layer` | 點擊地圖 feature 篩選 |
| `@clear-by-param-filter` | 清除參數篩選 |
| `@clear-by-layer-filter` | 清除圖層篩選 |
| `@fly` | 飛到指定座標 |
| `@info` | 顯示更多資訊 dialog |

---

### 步驟二：註冊路由

在 `src/router/index.js` 的 `routes` 陣列中新增路由，**預設加 `meta: { layout: "dashboard" }`** 以套用 NavBar + SideBar + SettingsBar 殼：

```js
import MyCustomView from "../views/MyCustomView.vue";

const routes = [
  // ...既有路由
  {
    path: "/my-custom",
    name: "my-custom",
    component: MyCustomView,
    meta: { layout: "dashboard" },     // ← 預設加這行
  },
];
```

---

### 步驟三：SideBar 加分頁 link（**強制**）

新頁面如果使用者找不到入口就等於沒做。在 `src/components/utilities/bars/SideBar.vue` 加 link：

```vue
<!-- 加在「公共儀表板」h1 之前；若已有「示範儀表板」section 直接補一條 link -->
<h1>{{ isExpanded ? `示範儀表板` : `示範` }}</h1>
<RouterLink
  :to="$route.path.startsWith('/my-custom') ? $route.path : '/my-custom'"
  class="sidebar-demo-link"
  active-class="sidebar-demo-link-active"
>
  <span :title="!isExpanded ? '我的頁面' : ''">dashboard</span>
  <h3 v-if="isExpanded">我的頁面</h3>
</RouterLink>
```

`to` 用三元式可以保留 sub-route（使用者在 `/my-custom/mapview` 時點 link 不會被踢回 `/my-custom`）。

樣式 `.sidebar-demo-link` / `.sidebar-demo-link-active` 已存在 SideBar.vue 的 scoped style，直接套用。

---

### 步驟四：（通常不用動）路由守衛

`router.beforeEach` 已經對 `meta.layout === "dashboard"` 自動處理（不清 currentDashboard、map 改用 clearOnlyLayers 而非 clearEntireMap）。**只在你的頁面有特殊需求時才動守衛**，例如要繞過行動裝置 redirect、要載特定 params 等。

---

### 步驟五：（通常不用動）App.vue layout

App.vue 已根據 `route.meta?.layout === "dashboard"` 自動套用主站殼。**只有當你需要新的 layout（非 dashboard、非 admin、非 component）時才動 App.vue**，這種情況請先在 `docs/` 寫架構決議。

---

### 步驟六：（選用）自行管理資料來源

如果你的頁面不走 contentStore 既有的 dashboard 流程，而是自行呼叫 API 取得組件資料，可以：

```js
import http from "../router/axios";

const myComponents = ref([]);

onMounted(async () => {
  // 取得特定組件
  const res = await http.get("/component/123/all");
  const component = res.data.data;

  // 取得圖表資料
  const chartRes = await http.get("/component/123/chart");
  component.chart_data = chartRes.data.data;

  myComponents.value.push(component);
});
```

注意：組件的 `config` 物件需包含以下結構才能被 `DashboardComponent` 正確渲染：

```js
{
  index: "component-index",
  name: "組件名稱",
  chart_config: {
    types: ["BarChart"],      // 圖表類型陣列
    color: ["#ff0000"],       // 顏色
    categories: [],           // 分類標籤
    unit: "",                 // 單位
  },
  chart_data: { /* 圖表資料，格式參見 .claude/skills/chart/reference/chart-data.md */ },
  map_config: [               // 地圖圖層配置陣列，無地圖則為 [null]
    {
      index: "layer-index",
      type: "circle",         // Mapbox 圖層類型
      city: "taipei",
      title: "圖層名稱",
      source: "geojson",
      paint: {},
      property: [],           // popup 顯示的欄位
    }
  ],
  map_filter: null,           // 地圖篩選設定
  history_config: null,       // 歷史資料設定
  time_from: "",
  time_to: "",
  update_freq: 0,
  update_freq_unit: "day",
}
```

---

## 提示給 Claude Code

當你要請 Claude Code 幫你建立新頁面時，可以提供以下資訊：

1. **頁面名稱與路由路徑**（例：`/dispatch-1999`）
2. **資料來源**：走既有 dashboard 流程，還是自行呼叫 API？
3. **組件清單**：每個組件的圖表類型（BarChart、ColumnChart 等）與是否有地圖
4. **Layout 需求**：左側組件 + 右側地圖（同 MapView），或純組件 grid（同 DashboardView）
5. **是否需要額外功能**：城市切換、收藏、定時更新等
