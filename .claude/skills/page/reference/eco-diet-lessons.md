# eco-diet 自訂多城市 / 多 layer view 踩過的坑

當 view 需要：
- **每個 component 獨立的城市下拉**（非共用 cityManager 設定）
- **自管 GeoJSON layer**（不走 mapStore 標準註冊流程）
- **同畫面多個 layer 同時開**

走這份 doc。範例完整在 `src/views/EcoDietView.vue`。

---

## 1. 自訂城市下拉，不動 cityManager

### 為什麼不直接改 cityManager

`src/dashboardComponent/utilities/cityManager.ts` 是**全站共用**：主站公共儀表板都吃同一份 selectList / tagList。改 metrotaipei 的 selectList 會影響所有頁面的雙北儀表板。

### 正解：view 自包選項

```js
// EcoDietView.vue
const CITY_SELECT_LIST = [
    { name: "臺北市", value: "taipei" },
    { name: "新北市", value: "newtaipei" },
    { name: "雙北", value: "metrotaipei" },
];
const CITY_LABEL = {           // BE 回傳的中文字串對照
    taipei: "臺北市",
    newtaipei: "新北市",
};

<DashboardComponent
    :select-btn="true"
    :select-btn-list="CITY_SELECT_LIST"   // ← 自包，不走 cityManager.getSelectList
    :active-city="activeCityMap[item.index]"
    @change-city="(city) => handleChangeCity(item, city)"
/>
```

## 2. 每組件獨立 activeCity（不能共用）

每張卡片 dropdown 應該**各自獨立**——使用者切 C1a 餐廳到「臺北」不該影響 C4 商店仍是「雙北」。

```js
const activeCityMap = reactive({
    eco_diet_restaurants_points:    "metrotaipei",
    eco_diet_restaurants_density:   "metrotaipei",
    // ... 每個 component.index 一條
});

function handleChangeCity(component, cityValue) {
    activeCityMap[component.index] = cityValue;
    component.city = cityValue;                    // 同步給 dialog 的「City: xxx」標題
    if (component.map_config?.[0]) {
        component.map_config[0].city = cityValue;  // 同步給地圖 layer city 標
    }
    switch (component.index) {
        case "...": recomputeXxx(); applyLayerCityFilter(...); break;
    }
}
```

## 3. tag 與資料同步（避開 cityManager 雙標籤陷阱）

`cityManager.getTagList("metrotaipei")` 預設回傳 `[雙北, 臺北市]` 雙標籤——主站歷史包袱（資料源最初只有臺北）。**自訂 view 不要直接吃**，否則切「新北」時還是會跳出「臺北市」tag 誤導使用者。

```js
// 顯示什麼資料就標什麼 tag
function tagListOf(component) {
    const cityValue = activeCityMap[component.index];
    if (cityValue === "taipei")    return [{ name: "臺北市", value: "taipei" }];
    if (cityValue === "newtaipei") return [{ name: "新北市", value: "newtaipei" }];
    return [{ name: "雙北", value: "metrotaipei" }];
}

<DashboardComponent :city-tag="tagListOf(item)" />
```

### MoreInfo dialog 也要同步

`MoreInfo.vue` 內部寫死用 `cityManager.getTagList(...)`。已加 `city_tag_override` fallback 欄位，自訂 view **務必**用這條：

```js
function handleMoreInfo(item) {
    dialogStore.showMoreInfo({
        ...item,
        city_tag_override: tagListOf(item),    // ← 不加會在 dialog 看到雙北+臺北市
    });
}
```

## 4. 圖表色：每組件固定 + 多 layer 不撞色

### 雙重需求

- **單組件內**：臺北綠／新北藍要固定（單城檢視時 color[0] 不能錯位）
- **多組件之間**：餐廳、商店、實物銀行三層同時打開時要分得出哪是哪

### 解法：CITY_COLOR per component + recompute 動態重排

```js
const CITY_COLOR = {
    eco_diet_restaurants_points:  { taipei: "#5fcf80", newtaipei: "#5a9cf8" },  // 綠/藍
    eco_diet_green_stores_points: { taipei: "#ec7cb1", newtaipei: "#67baca" },  // 粉/青
    eco_diet_food_banks_points:   { taipei: "#f6c344", newtaipei: "#a37cf6" },  // 黃/紫
};

function recomputeC1a() {
    const palette = CITY_COLOR.eco_diet_restaurants_points;
    const legend = [];
    const colors = [];
    if (city === "metrotaipei" || city === "taipei") {
        legend.push({ name: "臺北市", value: tpe });
        colors.push(palette.taipei);
    }
    if (city === "metrotaipei" || city === "newtaipei") {
        legend.push({ name: "新北市", value: ntp });
        colors.push(palette.newtaipei);
    }
    c1aComponent.value.chart_data = legend;
    c1aComponent.value.chart_config.color = colors;   // ← 同步重排，色序對齊 legend
}
```

地圖點 `circle-color` 也要用同一組色：

```js
const PAINT_BY_KEY = {
    restaurant: { "circle-color": ["match", ["get", "city"],
        "臺北市", "#5fcf80", "新北市", "#5a9cf8", "#888888"], ... },
    greenStore: { "circle-color": ["match", ["get", "city"],
        "臺北市", "#ec7cb1", "新北市", "#67baca", "#888888"], ... },
    foodBank:   { "circle-color": ["match", ["get", "city"],
        "臺北市", "#f6c344", "新北市", "#a37cf6", "#888888"], ... },
};
```

### 新北 tag 顏色

`globalStyles.css` 與 `chartStyles.css` 補了 `--color-newtaipei: #11ac78`，`ComponentTag.vue` 也加了 `&.newtaipei` class。沒加 → 新北 tag 變透明背景。

## 5. DashboardComponent `:key` 必帶 activeCity

```vue
<DashboardComponent
    v-for="item in allComponents"
    :key="`${item.index}-${activeCityMap[item.index]}`"   ← 必須
    ...
/>
```

**為什麼**：ApexCharts 包裝的 BarChart / DistrictChart 內部有 series 快取，光換 props.series 不會重畫（ColumnChart 的 chartOptions ref 在 mount 時 snapshot 就是個 hint）。把 activeCity 放進 key，城市切換時整個 DashboardComponent 重 mount，繞過快取問題。

**踩過**：C1b 行政區密度切換城市時看起來「壞掉」，就是這條沒加。

## 6. 自管 GeoJSON layer + hover popup（不走 mapStore 標準流程）

### mapStore 標準流程不適用的時機

`mapStore.addMapLayer()` 預期 layer 是 contentStore.dashboard 來源、有 `mapConfigs[layerId]` 註冊、走標準 click → `addPopup()` → `queryRenderedFeatures` 流程。自訂 view 跳過這條，是因為：
- 三個 layer 是 view 自管，不在 contentStore
- 想要 hover 顯示資料而非 click

### 自管 layer 範本

```js
import mapboxGl from "mapbox-gl";

async function ensureLayer(layerId, key) {
    await ensureMapReady();              // 等 mapStore.map.isStyleLoaded()
    if (mapStore.map.getSource(sourceId)) {
        mapStore.map.getSource(sourceId).setData(data);
        return;
    }
    mapStore.map.addSource(sourceId, { type: "geojson", data });
    mapStore.map.addLayer({ id: layerId, type: "circle", source: sourceId,
        layout: { visibility: "none" }, paint: PAINT_BY_KEY[key] });
    attachHoverPopup(layerId, key);     // ← 同時掛 hover handler
}

// 城市切換時用 setFilter 而不是重灌 source data
function applyLayerCityFilter(layerId, cityValue) {
    if (cityValue === "metrotaipei") {
        mapStore.map.setFilter(layerId, null);
    } else {
        mapStore.map.setFilter(layerId, ["==", ["get", "city"], CITY_LABEL[cityValue]]);
    }
}

// hover popup（共用一個實例，避免每次 mouseenter 都 new）
let hoverPopup = null;
function attachHoverPopup(layerId, key) {
    const map = mapStore.map;
    map.on("mouseenter", layerId, () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mousemove", layerId, (e) => {
        const f = e.features?.[0];
        if (!f) return;
        hoverPopup ??= new mapboxGl.Popup({ closeButton: false, closeOnClick: false, offset: 10 });
        hoverPopup.setLngLat(f.geometry.coordinates.slice())
            .setHTML(buildPopupHtml(key, f.properties))
            .addTo(map);
    });
    map.on("mouseleave", layerId, () => {
        map.getCanvas().style.cursor = "";
        hoverPopup?.remove();
    });
}
```

### Popup HTML XSS 防護

`feature.properties` 來自 BE，**必須** escapeHtml：

```js
function escapeHtml(str) {
    if (str == null) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
```

### onBeforeUnmount 清乾淨

```js
onBeforeUnmount(() => {
    if (hoverPopup) { hoverPopup.remove(); hoverPopup = null; }
    [LAYER_IDS].forEach((id) => {
        if (mapStore.map.getLayer(id)) mapStore.map.removeLayer(id);
        if (mapStore.map.getSource(`${id}-source`)) mapStore.map.removeSource(`${id}-source`);
    });
});
```

## 7. mapview tab 的「無空間資料組件」用 `mode="default"`

```vue
<!-- ❌ 錯：mode="map" 沒 toggle-on，圖表不會渲染（chart 區塊被 v-if 卡掉）-->
<DashboardComponent :config="item" mode="map" />

<!-- ✅ 對：用 default，預設展開、有下拉、無多餘 toggle -->
<DashboardComponent :config="item" mode="default" :info-btn="true"
    :select-btn="true" :select-btn-list="CITY_SELECT_LIST" />
```

無空間資料組件本來就沒地圖層好 toggle，硬用 `mode="map"` 變成使用者必須點一下開關才看得到內容（且開關沒有實際作用）。

## 8. 多 series time-series 不要硬塞 ColumnChart

C5 廢棄物趨勢一開始用 `ColumnChart` + 8 series × 6 年──結果年度 label / bar 寬度全擠壓變糊。

**判斷準則**：series 數 × categories 數 > 30 → 換 `TimelineSeparateChart`（折線圖比較）。線條疊在不同 Y 軸高度互不打架，年份標籤只 6 個點不會擁擠。

```js
// ColumnChart 吃 categories + data:[num,...]
{ types: ["ColumnChart"], categories: ["2018", ...], color: [...] }
[{ name: "臺北市-廚餘", data: [62458, 64320, ...] }, ...]

// TimelineSeparateChart 吃 [{x:ISO, y:num},...]，不需要 categories
{ types: ["TimelineSeparateChart"], color: [...] }
[{ name: "臺北市-廚餘", data: [{x:"2018-01-01T00:00:00+08:00", y:62458}, ...] }, ...]
```

## 9. mock plugin 切真 BE：移 routes 條目即可

`Taipei-City-Dashboard-FE/mock/index.js` 是 vite plugin，攔尚未實作的 BE 路由回傳本地 JSON。BE 真的實作完哪一條：

```js
// 從 routes map 把該條目刪掉
const routes = {
    // "/api/v1/eco_diet/restaurant/points": "eco-diet/restaurant-points.json",  ← 刪掉
    "/api/v1/eco_diet/restaurant/density-by-district": "...",  // 還沒實作的留著
};
```

**FE 不用改任何 view 程式碼**——`http instance baseURL` 走 vite proxy，刪掉 mock 條目後請求自動轉發到真 BE。

## 10. http instance 必用 `baseURL: ""` override

```js
import http from "../router/axios";

function ecoApi(path) {
    return http.get(path, { baseURL: "" });   // ← 必須 override 成空字串
}
```

`http` instance 的 `baseURL = VITE_API_URL` 預設指向 prod（`/api/dev`）。打本機 BE 的 `/api/v1/*` 要把 baseURL 蓋掉，否則 URL 會變成 `/api/dev/api/v1/eco_diet/...` 找不到。

mock plugin 攔的也是相對路徑，所以一併要走 override。

## 完成後檢查清單（多城市自訂 view 專屬）

- [ ] CITY_SELECT_LIST 自包，沒動 cityManager.ts
- [ ] activeCityMap reactive，每個 component.index 一條 entry
- [ ] handleChangeCity 同步 component.city + map_config[0].city + recompute + setFilter
- [ ] tagListOf 動態返回單城 tag，避開雙北雙標籤
- [ ] handleMoreInfo 注入 city_tag_override
- [ ] CITY_COLOR per component，多 layer 配色不撞
- [ ] recompute 同步重排 chart_config.color 順序
- [ ] DashboardComponent :key 含 activeCity
- [ ] hover popup escapeHtml + 共用單一 instance + onBeforeUnmount 清掉
- [ ] mapview noMap 區段用 mode="default"，hasMap 才用 mode="map"
- [ ] http instance 加 `baseURL: ""` override
