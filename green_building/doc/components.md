# green_building 組件說明

> 將「綠建築標章」資料製成子查詢組件 921/922，並以 **923 `green_buildings`（multi_chart）**
> 合併「行政區圖」「長條圖(%)」「縱向堆疊長條圖」三種視圖，加入「永續環境」儀表板（905/906），
> 同時支援「臺北市」與「雙北」城市切換。

## 一、原始資料

| 檔案 | 說明 |
| --- | --- |
| `green_geocoded.csv` | 1394 筆綠建築標章（含 `valid='1'` 共 680 筆：臺北市 357、新北市 323） |
| `green_geocoded.geojson` | 同上，每個 feature 含 `行政區`／`ditrict`／`valid`／`rank` 等屬性 |

關鍵欄位：

- `valid`（字串 `'1'`／`'0'`）：認可是否仍有效
- `rank`（整數 1~5）：1=合格級、2=銅級、3=銀級、4=黃金級、5=鑽石級
- `行政區`（CSV 欄）→ DB `city`：「臺北市」／「新北市」（少量「台北市」）
- `ditrict`（CSV 欄，原始拼字保留）→ DB `district`：「大安區」等

## 二、組件設計

| 組件 ID | `components.index` | 名稱 | 圖表 | 地圖 |
| ---: | --- | --- | --- | --- |
| 921 | `green_buildings_district` | 綠建築 - 各行政區棟數分布 | DistrictChart | ✅ 兩個 layer |
| 922 | `green_buildings_rank` | 綠建築 - 認可等級結構 | BarPercentChart（橫向 100% 堆疊）等 | — |
| 923 | `green_buildings` | 綠建築（合併視圖） | DistrictChart、BarPercentChart、ColumnChart（縱向堆疊，單位棟） | ✅ 同 921 |

儀表板僅掛 **923**。`query_charts`：`921`/`922` 各 `taipei`+`metrotaipei`；`923` 為 `multi_chart` bundle，
其中 **BarPercentChart** 與 **ColumnChart** 皆指向 922 的 **three_d** 查詢（行政區 × 等級棟數；`ORDER BY rank_val ASC` 使堆疊由底至頂為合格→鑽石）。

`query_charts` 兩個子 index 皆寫入 `taipei` / `metrotaipei` 各一筆；923 再 2 筆（共 6 筆與 923 相關 + 921/922 各 2 筆）。

### 921 `green_buildings_district`

- **DistrictChart**：依行政區數值映射深淺。
  - `taipei`：12 區 `valid='1' AND city='臺北市'` 棟數
  - `metrotaipei`：41 區 `valid='1'`（含臺北＋新北）棟數
- **地圖（2 個 component_maps，皆掛在 index `green_buildings_district`）**：
  - Layer 1（`type=circle`）：`valid='1' AND rank≠5`（鑽石級不畫圓點，避免與葉子重疊）
  - Layer 2（`type=symbol`, `icon='leaf-icon'`）：`valid='1' AND rank=5` 鑽石級葉子
- **GeoJSON 檔名**（必須與 `component_maps.index` 一致）：
  `Taipei-City-Dashboard-FE/public/mapData/green_buildings_district.geojson`
- **`map_filter`**：`{"mode":"byParam","byParam":{"xParam":"ditrict"}}`
  → 點擊行政區圖時，地圖以 GeoJSON property `ditrict` 篩選對應區。

### 922 `green_buildings_rank`

- **three_d 查詢**：每個行政區 × 五個認可等級之 **棟數**（`valid='1'`），供 multi_chart 的 BarPercentChart / ColumnChart 共用。
- **無地圖**（子查詢時 `map_config_ids='{}'`）。
- 儀表板若僅使用 923，可不單獨顯示 922。

### 923 `green_buildings`（multi_chart）

- **DistrictChart**：同 921。
- **BarPercentChart**：橫軸為各區總長 100%，分段為五級占比。
- **ColumnChart**（`chart stacked: true`）：橫軸行政區、縱軸棟數，五級由下而上為合格→鑽石（與官方 **three_d** 說明一致）。

## 三、前端 leaf-icon 注入

symbol layer 用的 `leaf-icon` 已在 `Taipei-City-Dashboard-FE/src/store/mapStore.js`
的 `addSymbolSources()` 內注入：以 inline SVG 經 `Blob` → `URL.createObjectURL` →
`Image.onload` → `map.addImage('leaf-icon', img)`，地圖載入後自動可用。

## 四、灌入步驟

```bash
# 1. dashboard DB：建表
docker exec -i postgres-data psql -U postgres -d dashboard \
  < green_building/output/seed/01_dashboard_data.sql

# 2. dashboard DB：載入 CSV
docker cp green_building/green_geocoded.csv postgres-data:/tmp/green.csv
docker exec -i postgres-data psql -U postgres -d dashboard -c \
  "\copy public.green_buildings(building_no, building_name, building_desc, cert_version, cert_level, rank, valid_until, valid, cert_type, designer, city, district, lot_number, building_use, lon, lat) FROM '/tmp/green.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')"

# 3. dashboardmanager DB：組件設定
docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
  < green_building/output/seed/02_dashboardmanager_components.sql

# 3b.（若已存在 923）為 multi_chart 加上「縱向堆疊長條圖」視圖
docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
  < green_building/output/seed/03_green_buildings_add_column_stacked.sql

# 4. FE 靜態 GeoJSON
cp green_building/green_geocoded.geojson \
   Taipei-City-Dashboard-FE/public/mapData/green_buildings_district.geojson

# 5. 永續環境儀表板（會把 921/922 加進 dashboards.components）
docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
  < component_doc/seed/03_sustainable_env_dashboard.sql
```

## 五、驗證

```sql
-- dashboard DB
SELECT city, COUNT(*) FILTER (WHERE valid='1') FROM public.green_buildings GROUP BY city;
-- 預期：臺北市 357、新北市 323（合計 680）

SELECT rank, COUNT(*) FROM public.green_buildings WHERE valid='1' GROUP BY rank ORDER BY rank;
-- 預期：1=130, 2=61, 3=312, 4=127, 5=47

-- dashboardmanager DB
SELECT index, city, query_type, array_length(map_config_ids,1) AS layers
FROM public.query_charts WHERE index LIKE 'green_buildings%'
ORDER BY index, city;
-- 預期：district×2 (layers=2)、rank×2 (layers=NULL)

SELECT components FROM public.dashboards WHERE id IN (905,906);
-- 預期：{901,902,903,911,912,913,914,921,922}
```

## 六、切換圖表後「全部變葉子」（已於 FE 修正）

`changeActiveChart` 會呼叫 `clearByParamFilter`，舊版對每個圖層 `setFilter(null)`，會**洗掉** symbol 層原本的 `rank=5` 條件，導致葉子套用到所有點。  
現已改為：**清除互動篩選時還原 `map_config.paint.filter` 基底條件**；`filterByParam` 亦改為在基底 filter 上 **AND** 行政區條件（見 `mapStore.js` 的 `getLayerBaseFilter` / `mergeMapFeatureFilters`）。

## 七、葉子 icon 不顯示時（已於 FE 修正）

經檢查 **不是** GeoJSON `rank` 型別問題（JSON 中皆為 **number**，與 filter `5` 一致）。

真正原因為兩點（已修在 `Taipei-City-Dashboard-FE/src/store/mapStore.js`）：

1. **paint JSON 結構**：`component_maps` 將 `layout`、`filter` 放在 `paint` 物件內；舊版 `addMapLayer` 把它們整包 merge 進 Mapbox 的 `paint`，導致 **`icon-image` 未進入圖層 `layout`**、`filter` 亦非圖層頂層，symbol layer 無效。
2. **時序**：`leaf-icon` 以 `Image.onload` 非同步 `addImage`，`addSymbolSources` 未等待即繼續，圖層有機會在 **icon 註冊前** 建立。現改為開頭 **`await registerInlineSvgIcons()`**。

## 八、與 `green_buildings_upload.sql` 的差異

原 `green_building/green_buildings_upload.sql` 的設計問題（已修正）：

1. 兩種圖表（DistrictChart 12/41 區 vs. HorizontalBarChart 5 ranks）資料形狀不同，
   無法共用一個 `query_chart`，必須**拆成兩個 component**。
2. `query_charts.city='rank_dist'` 是非法值；`city` 欄位是給 FE cityManager
   切換用，只能是 `taipei`/`metrotaipei`/`newtaipei`。
3. `BarChart` 是 FE 標準的橫向長條圖（`HorizontalBarChart` 並非標準 chart type
   的 PascalCase；專案實作中以 `BarChart` 做橫向長條）。
