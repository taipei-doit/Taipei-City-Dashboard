# 地圖交叉比對圖例解析邏輯

## 目的

依據元件的 `map_config` 自動產生「地圖交叉比對」左下角圖例，讓圖例與實際 Mapbox／Deck.gl 圖徵的顏色、形狀及 icon 保持一致。

分析資料來源：

- `docs/component_maps_202610281123.xlsx`
- `src/store/mapStore.js`
- `src/assets/configs/mapbox/mapConfig.js`
- `src/assets/utilityFunctions/parseMapConfigs.js`
- `src/components/map/MapContainer.vue`

附檔共有 185 筆圖層設定。依本文件規則，其中 176 筆應提供圖例，另外 9 筆依需求不提供圖例。

## 實作狀態

目前圖例解析與 UI 已完成調整：

- `src/assets/utilityFunctions/parseMapConfigs.js`
  - 以 `buildMapLegend(config)` 作為主要入口
  - 支援固定色、`match`、`case`、`interpolate`、`step`
  - 支援 arc 雙色、空心 circle、line 虛線與 symbol 本地 icon
  - 使用圖徵 type 白名單排除不提供圖例的類型
- `src/components/map/MapContainer.vue`
  - 依 `currentVisibleLayers` 建立圖例群組
  - 支援圓、面、線、虛線、arc 雙色、連續色階與實體圖片
  - 圖層沒有可用圖例時不建立空群組
- `src/store/mapStore.js`
  - 使用 `legendType` 保留原始圖徵類型
  - isoline／voronoi 轉成 line 渲染後仍可正確排除
  - isoline 改用 paint 副本，不再刪除原始設定內容

驗證結果：

- 附檔總數：185 筆
- 預期提供圖例：176 筆
- 實際成功產生：176 筆
- 解析失敗：0 筆

## 輸入資料

每個圖層使用一筆 `map_config`，圖例主要使用以下欄位：

- `title`：圖例群組標題
- `type`：原始圖徵類型
- `paint`：顏色、透明度、線寬及 Mapbox expression
- `icon`：symbol 使用的本地 icon 識別字
- `property`：資料欄位 key 與中文名稱，可用於圖例標籤

`size` 與 `circle-radius` 不進入圖例，圖例只對照顏色、形狀與 icon。

圖層 ID 目前由下列格式組成：

```text
{index}-{type}-{city}
```

圖例判斷應使用原始 `map_config.type`，不能只從實際 Mapbox layer type 或字串拆解 layer ID 推斷。

## 解析輸出格式

解析後統一輸出圖例群組：

```js
{
	title: "圖層名稱",
	type: "circle",
	items: [
		{
			label: "圖例文字",
			kind: "circle",
			color: "#ff5722",
			colors: null,
			iconSrc: null,
			opacity: 1,
			hollow: false,
			dashed: false,
			continuous: false,
		},
	],
}
```

欄位說明：

- `label`：分類、數值區間或「全部」
- `kind`：圖例視覺類型，例如 `circle`、`fill`、`line`、`arc`、`symbol`
- `color`：單一顏色
- `colors`：arc 雙色或連續色階
- `iconSrc`：symbol 本地端圖片路徑
- `opacity`：圖例透明度
- `hollow`：是否為空心 circle
- `dashed`：是否為虛線
- `continuous`：是否為 interpolate 連續色階

解析層只輸出資料結構，不直接輸出 Vue template；`MapContainer.vue` 再依 `kind` 繪製對應圖徵。

## 整體解析流程

```text
可見圖層 layerId
  -> 取得 mapStore.mapConfigs[layerId]
  -> 讀取原始 legendType / originalType
  -> 判斷是否提供圖例
  -> 依 type 找出主要樣式欄位
  -> 解析固定值或 Mapbox expression
  -> 補入圖徵形狀、透明度、線型或本地 icon
  -> 移除無效／重複項目
  -> items 不為空時才加入圖例群組
```

目前入口函式：

```js
buildMapLegend(mapConfig)
```

不建議繼續只使用：

```js
parseLegendFromPaint(paint)
```

原因是圖例不只依賴 `paint`，還需要 `type`、`icon`、`property` 與原始圖徵類型。`size` 與 `circle-radius` 不進入圖例。

## 圖徵類型規則

### `arc`

提供圖例。

資料來源：

- `paint["arc-color"]`
- `paint["arc-width"]`
- `paint["arc-opacity"]`

`arc-color` 在目前附檔中是色彩陣列，不是 Mapbox expression：

```js
["#fd7900", "#47d3d9"]
```

解析規則：

- 一個顏色：顯示單色弧線
- 兩個顏色：顯示由起點色到終點色的方向弧線或漸變線
- 沒有顏色：回退 `#ffffff`
- `arc-width` 只影響圖例線條粗細，不產生額外圖例項目
- `arc-animate` 不影響圖例內容

### `circle`

提供圖例，使用圓形圖徵。

主要樣式欄位：

```js
paint["circle-color"]
```

輔助欄位：

- `circle-opacity`
- `circle-radius`
- `circle-stroke-color`
- `circle-stroke-width`

解析規則：

1. 優先解析 `circle-color`。
2. `circle-stroke-color` 只作為圓形外框，不另外建立一組分類。
3. 若沒有 `circle-color` 或 `circle-opacity` 為 `0`，但有 `circle-stroke-color`，則繪製空心圓圖例。
4. `circle-radius` 不產生圖例。圖例只顯示顏色對照，不依半徑做大小分級。

附檔中的「緊急避難設施」只有 `circle-stroke-color`，是必須支援空心圓的實際案例。

### `fill`

提供圖例，使用 2D 方形或矩形色塊。

主要樣式欄位：

```js
paint["fill-color"]
```

輔助欄位：

- `fill-opacity`
- `fill-outline-color`

解析規則：

- 只使用 `fill-color` 產生分類。
- `fill-outline-color` 只作為色塊外框，不產生第二組圖例。
- 沒有設定 `fill-opacity` 時，可採 Mapbox 共用預設值或圖例 UI 預設值。

### `fill-extrusion`

提供圖例，但依需求以 2D 色塊呈現，不繪製立體柱狀圖例。

主要樣式欄位：

```js
paint["fill-extrusion-color"]
```

輔助欄位：

- `fill-extrusion-opacity`

不需要解析：

- `fill-extrusion-height`
- `fill-extrusion-base`

高度只影響地圖上的 3D 外觀，不影響圖例分類。

目前附檔中的 `fill-extrusion-color` 包含：

- `match`
- `interpolate`
- `step`

因此這三種 expression 都必須支援。

### `isoline`

不提供圖例。

注意：`AddIsolineMapLayer()` 會把渲染設定的 `type` 改成 `line` 後交給 `addMapLayer()`。若 `mapStore.mapConfigs` 最後保存的是改寫後設定，圖例端會誤判為一般 `line`。

必須保存原始類型，例如：

```js
{
	type: "line",
	legendType: "isoline",
}
```

或將原始設定與渲染設定分開保存。

### `line`

提供圖例，使用水平線段。

主要樣式欄位：

```js
paint["line-color"]
```

輔助欄位：

- `line-opacity`
- `line-width`
- `line-dasharray`
- `icon === "dash"`

解析規則：

- `line-color` 決定分類。
- `line-width` 只調整圖例線條粗細，不產生額外項目。
- 有 `line-dasharray` 或 `icon === "dash"` 時，使用虛線圖例。
- 依 zoom 變化的 `line-width` 不需要轉成圖例分類。

### `symbol`

提供圖例，使用本地端實體 icon。

主要資料來源是：

```js
mapConfig.icon
```

不能要求 `paint` 一定存在。附檔中 16 筆 symbol 有 10 筆沒有 `paint`，若先判斷 `paint` 是否存在，這些圖例會全部消失。

靜態 icon 可解析為：

```text
/images/map/{icon}.png
```

目前附檔包含：

- `triangle_white`
- `triangle_green`
- `bus`
- `cctv`
- `metro`
- `live`
- `youbike_elec`

建議建立明確的 icon registry：

```js
const MAP_LEGEND_ICONS = {
	triangle_white: "/images/map/triangle_white.png",
	triangle_green: "/images/map/triangle_green.png",
	bus: "/images/map/bus.png",
	cctv: "/images/map/cctv.png",
	metro: "/images/map/metro.png",
	live: "/images/map/live.png",
	youbike_elec: "/images/map/youbike_elec.png",
	bike_red: "/images/map/bike_red.png",
	bike_orange: "/images/map/bike_orange.png",
	bike_green: "/images/map/bike_green.png",
}
```

使用 registry 的優點：

- 可以確認 icon 確實存在於本地端
- 避免任意字串組成路徑
- 可集中處理缺圖 fallback
- 可處理設定名稱與實際檔名不同的情況

#### `youbike` 特例

`icon === "youbike"` 並不是實際檔名。實際渲染由 `maplayerCommonLayout["symbol-youbike"]["icon-image"]` 的 `case` expression 決定：

```js
[
	"case",
	["==", ["get", "available_return_bikes"], 0],
	"bike_red",
	["==", ["get", "available_rent_general_bikes"], 0],
	"bike_orange",
	"bike_green",
]
```

應產生三筆圖例：

- `bike_red`：無可還車位
- `bike_orange`：無一般自行車可借
- `bike_green`：可借且可還

不能嘗試讀取不存在的 `/images/map/youbike.png`。

### `symbol-3d`

不提供圖例。

即使低 zoom 時會顯示 2D circle，仍依原始需求排除。

### `voronoi`

不提供圖例。

注意：`AddVoronoiMapLayer()` 會把 `type` 改成 `line` 後渲染，與 isoline 有相同誤判風險。圖例端必須使用原始類型。

### `wind-heat`

提供固定圖例，不解析 DB paint。

色碼與 `useWindEngine.js` 的熱區 `fill-color` 共用 `WIND_HEAT_COLOR_STOPS`。顏色對應的是目前畫面裡的相對風經過頻率，不是固定次數：

```text
低 frequency 0     -> rgba(255,80,80,0.4)
                 0.15 -> rgba(255,160,80,0.4)
                 0.35 -> rgba(160,220,255,0.4)
高 frequency 0.7 以上 -> rgba(0,170,255,0.6)
```

圖例標籤為「風經過頻率：低 – 高」。

## 圖例提供判斷

建議先建立白名單與排除清單：

```js
const LEGEND_TYPES = new Set([
	"arc",
	"circle",
	"fill",
	"fill-extrusion",
	"line",
	"symbol",
])

const NO_LEGEND_TYPES = new Set([
	"isoline",
	"symbol-3d",
	"voronoi",
])
```

優先使用白名單。未來新增 type 時，未知類型預設不顯示，比錯誤繪製安全。

## Paint 主色欄位

每種 type 只能選一個主要顏色欄位：

```js
const PRIMARY_COLOR_KEYS = {
	arc: "arc-color",
	circle: "circle-color",
	fill: "fill-color",
	"fill-extrusion": "fill-extrusion-color",
	line: "line-color",
}
```

不能使用舊式 `parseLegendFromPaint()` 的做法遍歷所有名稱包含 `color` 的欄位，否則會發生：

- `circle-color` 與 `circle-stroke-color` 各產生一筆「全部」
- `fill-color` 與 `fill-outline-color` 各產生一組分類
- 描邊色被誤認為資料分類

stroke 與 outline 應合併到同一個圖例圖徵的外觀。

## Mapbox expression 解析

### 固定色

輸入：

```js
"#ff5722"
```

輸出：

```js
[
	{
		label: "全部",
		color: "#ff5722",
	},
]
```

### `match`

輸入：

```js
[
	"match",
	["get", "type"],
	"市區",
	"#a0b8e8",
	"河濱",
	"#b7ff98",
	"red",
]
```

輸出：

```text
市區  -> #a0b8e8
河濱  -> #b7ff98
```

解析方式：

1. `expression[1]` 是輸入欄位。
2. 從 `expression[2]` 開始，每兩個值是一組「分類值、顏色」。
3. 最後一個值是 Mapbox 必填的 fallback color。分類值本身沒有「其他」時，不把這個顏色顯示成圖例。只有某個分類值就是「其他」時，才會出現這一列。
4. 若分類值是陣列，代表多個值共用同一顏色，可使用頓號連接。

### `case`

Mapbox `case` 使用 first-match 語意，前面的條件成立後就不再判斷後續條件。

輸入：

```js
[
	"case",
	["<=", ["get", "times"], 3],
	"#5A1846",
	["<=", ["get", "times"], 14],
	"#831A3D",
	["<=", ["get", "times"], 75],
	"#E3611C",
	"#FFC300",
]
```

正確圖例標籤應為：

```text
≤ 3
> 3 且 ≤ 14
> 14 且 ≤ 75
> 75
```

不能直接顯示：

```text
≤ 3
≤ 14
≤ 75
其他
```

後者沒有反映 first-match 後形成的互斥區間。無法收成這種區間時，最後的 fallback color 也不再標成「其他」，直接不顯示。

#### 條件格式化

需要遞迴支援：

- `==`
- `<`
- `<=`
- `>`
- `>=`
- `all`
- `any`，即使目前附檔未使用也可一併支援

例如：

```js
[
	"all",
	[">=", ["get", "person_capacity"], 100],
	["<", ["get", "person_capacity"], 1000],
]
```

應顯示：

```text
≥ 100 且 < 1000
```

不能只顯示「區間」。

### `interpolate`

輸入：

```js
[
	"interpolate",
	["linear"],
	["get", "aqi"],
	0,
	"#color-1",
	50,
	"#color-2",
	100,
	"#color-3",
]
```

`interpolate` 代表連續色階，不是離散分類。

建議圖例：

- 顯示一條連續漸層帶
- 左右標示最小值與最大值
- 中間 stop 可作為刻度
- 若 UI 暫時只能顯示色塊，可先列出 stops，但應標記為連續值

解析位置：

- `expression[2]`：資料輸入 expression
- `expression[3]` 起：每兩個值為 stop 與 color

如果輸入是 `["zoom"]`，代表顏色只依地圖縮放改變，不是資料分類，原則上不應生成多筆數值圖例，可退回單筆「全部」。

目前附檔的顏色 interpolate 都是依 feature 資料值運算，可生成連續色階。

### `step`

輸入格式：

```js
[
	"step",
	input,
	defaultColor,
	stop1,
	color1,
	stop2,
	color2,
]
```

圖例區間應為：

```text
< stop1              -> defaultColor
≥ stop1 且 < stop2   -> color1
≥ stop2              -> color2
```

目前 `parseStepExpression()` 已依上述規則實作，附檔中的 fill-extrusion `step` 設定可正常產生離散級距。

## 數值欄位名稱

expression 的資料輸入可能是：

```js
["get", "population"]
["to-number", ["get", "occupied_rate"]]
["coalesce", ["get", "population"], 0]
["+", ["to-number", ["get", "age_0"]], ["to-number", ["get", "age_1"]]]
```

建議遞迴尋找 expression 中的 `["get", key]`：

1. 找到單一 key 時，從 `mapConfig.property` 尋找相同 key 的中文 `name`。
2. 找不到中文名稱時，顯示原始 key。
3. 多欄位運算時，可只顯示區間值，不強制產生欄位名稱。
4. 欄位名稱適合放在色階標題或 tooltip，不必重複加在每一筆 label。

## 樣式合併順序

實際地圖樣式不是只使用 `mapConfig.paint`，目前 `addMapLayer()` 的合併順序是：

```text
maplayerCommonPaint[type]
  -> maplayerCommonPaint[type-icon]
  -> maplayerCommonPaint[type-size]
  -> mapConfig.paint
```

layout 的順序也相同。

目前附檔所有需要顯示圖例的非 symbol 圖層，都已在 `mapConfig.paint` 提供主要顏色，因此解析器直接使用 DB 的 paint；共用樣式主要控制半徑、線寬與縮放行為，不影響分類色彩。

symbol 則使用前端 `MAP_LEGEND_ICONS` registry 解析本地圖片，`youbike` 依現行 `symbol-youbike` layout 語意產生紅、橘、綠三種狀態。

若未來把主要顏色移到 `maplayerCommonPaint`，解析器需再依上述順序建立 `effectivePaint`，否則圖例會缺少共用預設色。

## 原始 type 與渲染 type

目前存在兩種 type 概念：

- 原始 type：後台設定的圖徵類別，也是圖例需求判斷依據
- 渲染 type：真正傳給 Mapbox 的 layer type

例如：

```text
isoline -> line
voronoi -> line
symbol-3d -> custom，低 zoom 時另建 circle
```

目前實作使用 `legendType` 保存原始類型：

```js
{
	type: "line",
	legendType: "isoline",
}
```

`buildMapLegend()` 的判斷順序是：

```js
config.legendType || config.originalType || config.type
```

因此地圖可以使用 `line` 渲染，圖例仍會依 `isoline` 或 `voronoi` 規則排除。

不建議從 layer ID 用 `split("-")` 取 type，原因是 `index` 與 type 本身都可能含有連字號，例如：

- `fill-extrusion`
- `symbol-3d`
- `wind-heat`

## 圖例群組建立

`MapContainer.vue` 可依可見圖層建立群組：

```js
const legendItems = computed(() => {
	return mapStore.currentVisibleLayers
		.map((layerId) => {
			const config = mapStore.mapConfigs[layerId]
			return buildMapLegend(config)
		})
		.filter((group) => group && group.items.length > 0)
})
```

必要行為：

- 只顯示 `currentVisibleLayers`
- 圖層關閉後立即移除對應圖例
- 排除類型不建立空群組
- 解析結果為空時不顯示標題
- 可見圖層順序應與地圖圖層清單一致

## Fallback 規則

目前依序處理：

1. 無 config：跳過。
2. type 不在白名單：跳過。
3. symbol icon 不存在於 registry：跳過該圖例群組。
4. paint 主色不存在：
   - circle 有 stroke color：畫空心圓
   - arc：回退白色
   - 其他類型：跳過
5. expression 不支援：回傳空陣列，不拋出例外。
6. expression 產生重複項目：以 `label + color + iconSrc` 去重。
7. template 僅渲染 `items.length > 0` 的群組。

## 現行程式行為

### `parseMapConfigs.js`

`buildMapLegend(config)` 會：

- 以 `legendType / originalType / type` 判斷原始圖徵類型
- 只解析各 type 對應的主要 color 欄位
- 將 stroke／outline 合併為圖徵外觀，不重複建立分類
- 將連續門檻 `case` 轉成互斥區間
- 將 `all`／`any` 條件遞迴轉成可讀文字
- 將 `interpolate` 輸出為連續色階
- 將 `step` 輸出為離散區間
- 將 symbol icon 解析為本地端圖片路徑
- `wind-heat` 使用固定頻率色階，不讀 paint

舊的 `parseLegendFromPaint(paint)` 暫時保留相容性，但 `MapContainer.vue` 已不再使用。

### `MapContainer.vue`

目前 computed 會將每個可見圖層交給 `buildMapLegend()`，並排除空群組。

template 已支援：

- 實心與空心 circle
- fill 與 fill-extrusion 的 2D 色塊
- line 實線與虛線
- arc 單色與雙色
- interpolate 連續漸層
- symbol 本地圖片

### `mapStore.js`

`addToMapLayerList()` 會在載入時保存 `legendType`。isoline 與 voronoi 即使改成 `line` 渲染，仍保留原始類型。

`AddIsolineMapLayer()` 會複製 `paint` 成 `renderPaint`，只從渲染副本移除 isoline 專用欄位，不再修改來源 config。

## 現行函式拆分

```text
buildMapLegend(config)
  ├─ parseSymbolLegend(config)
  ├─ parseArcLegend(config)
  └─ parseMapboxLegend(config, type)
       └─ parseColorValue(value)
          ├─ parseMatchExpression()
          ├─ parseCaseExpression()
          ├─ parseInterpolateExpression()
          ├─ parseStepExpression()
          └─ formatCondition()
```

解析結果再由 `MapContainer.vue` 的 `getLegendMarkerStyle()` 與 template 負責繪製，資料解析與 Vue UI 已分離。

## DB 資訊是否足夠

### 目前資料

目前 DB／附檔提供的資訊足以完成本次需求，不需要強制增加欄位。

必要資訊為：

- `title`
- 原始 `type`
- `paint`
- symbol 使用的 `icon`

`property` 可作為日後增加單位或欄位名稱的輔助資訊，但不是目前圖例生成的必要條件。`size` 與圓點半徑不產生大小分級圖例。

185 筆設定已全部驗證，其中 176 筆應提供圖例的設定皆成功解析，表示目前資料覆蓋本次規格。

### 前端仍負責的資訊

目前 DB 並非完全自描述，以下資訊仍由前端維護：

- icon 名稱與 `/images/map/*.png` 的實體路徑
- `youbike` 對應 `bike_red / bike_orange / bike_green`
- YouBike 三種狀態的中文標籤
- 哪些 type 不提供圖例

只要這些規則維持在前端，DB 不需要改動。

### 選配擴充

若未來希望新增特殊圖例時不修改前端，可增加選填 `legend_config` JSON 欄位：

```json
{
	"enabled": true,
	"title": "自訂圖例標題",
	"mode": "auto",
	"items": [
		{
			"label": "分類名稱",
			"color": "#ffffff",
			"icon": "icon_name"
		}
	]
}
```

建議維持選填：

- 沒有 `legend_config`：沿用目前自動解析
- `enabled: false`：明確關閉圖例
- 有 `items`：覆蓋自動解析，供特殊圖層使用

現階段不建議為所有圖層重複儲存圖例項目，避免 paint 與 legend 設定產生兩份顏色來源。

## 建議測試案例

至少覆蓋以下案例：

1. 固定色 circle。
2. 只有 stroke color 的空心 circle。
3. 固定色 fill 與 outline。
4. `match` fill。
5. 連續門檻 `case`。
6. 含 `all` 條件的 `case`。
7. `interpolate` 連續色階。
8. `step` fill-extrusion。
9. arc 單色與雙色陣列。
10. 靜態 symbol icon。
11. 動態 youbike 三 icon。
12. symbol 沒有 paint。
13. isoline 被轉成 line 後仍不顯示。
14. voronoi 被轉成 line 後仍不顯示。
15. symbol-3d 不顯示；wind-heat 顯示固定頻率色階。
16. 缺少 icon 檔案時的 fallback。
17. 不支援 expression 時不拋出例外。
18. 關閉可見圖層後同步移除圖例。

## 一句話總結

現行地圖圖例會以「原始圖徵 type」決定是否顯示及使用何種形狀，再從 DB paint 解析主色與 expression，或從前端 icon registry 取得本地圖片；目前 DB 資訊足以支援全部既有設定。
