# 村里人口密度（基本圖層）

新增雙北「村里人口密度」**基本圖層**（base layer）。
基本圖層是只在「地圖交叉比對」頁面左側才會出現、可疊加於任何主題地圖之上的輔助圖資（如自行車道、公車捷運站、人行道分布等同類）。

> 機制：基本圖層其實就是 index 為 `map-layers-taipei` / `map-layers-metrotaipei`
> 的特殊儀表板。前端進入「地圖交叉比對」頁面時自動抓
> `/dashboard/map-layers-{city}`，該儀表板 `components` 陣列裡的組件，就會
> 出現在左側「基本圖層」區塊。組件本身寫法與一般組件完全相同。

---

## 設計重點

| 欄位                  | 值                                                                                                                          |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `components.id`       | `941`                                                                                                                       |
| `components.index`    | `metrotaipei_village_population_density`                                                                                    |
| `components.name`     | `村里人口密度`                                                                                                              |
| 圖表類型              | `MapLegend`（基本圖層僅顯示圖例 / 單位）                                                                                    |
| 地圖類型              | `fill`（多邊形：村里界）                                                                                                    |
| `paint`               | `{"fill-color": "#000000", "fill-opacity": 0}`（**透明**，僅用於 popup 點擊互動）                                           |
| `property`            | `county`、`town`、`village`、`population`、`households`、`area_km2`、`density_per_km2`（含中文 name 與單位）                |
| `query_type`          | `map_legend`                                                                                                                |
| `city`                | 雙寫 `taipei` 與 `metrotaipei`（皆指向同一個 fill 圖層；資料本身已含雙北全部村里）                                          |
| 掛載到的儀表板        | `dashboards.id = 106` (`map-layers-taipei`) 與 `dashboards.id = 359` (`map-layers-metrotaipei`)                             |

`fill-opacity = 0` 但仍可點擊：Mapbox 的 `queryRenderedFeatures` 對於透明
但仍處於 `visibility: visible` 的圖層仍會回傳 feature，因此 popup 互動不受影響。

---

## 檔案結構

```
people-density/
├── README.md                                              ← 本檔
├── config.txt                                             ← 設計建議（component_maps 設定）
├── 基本圖層的設定方法.txt                                  ← 機制說明
├── metrotaipei_village_population_density.geojson         ← 來源 GeoJSON（雙北村里界 + 屬性）
└── output/
    └── seed/
        ├── 02_dashboardmanager_components.sql             ← 註冊組件 / chart / map / query
        └── 03_map_layers_dashboard.sql                    ← 將 941 掛入 map-layers-* 儀表板
```

GeoJSON 已複製到前端：

```
Taipei-City-Dashboard-FE/public/mapData/metrotaipei_village_population_density.geojson
```

> 慣例：`component_maps.index` 必須與 `public/mapData/{index}.geojson` 檔名一致。

---

## 灌入順序（Docker；對應 `docker/.env` 預設容器名）

本組件**沒有事實表**（基本圖層不需要 `dashboard` DB 的 raw 資料表），
僅需在 `dashboardmanager` 註冊組件並掛上 `map-layers-*` 儀表板：

```bash
# 1. 註冊組件（components / component_charts / component_maps / query_charts）
docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
  < people-density/output/seed/02_dashboardmanager_components.sql

# 2. 將組件掛入「基本圖層」儀表板（map-layers-taipei / map-layers-metrotaipei）
docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
  < people-density/output/seed/03_map_layers_dashboard.sql
```

兩支 SQL 皆**冪等**（重跑不會重覆插入；Step 2 用 `DISTINCT` 合併陣列）。

### 非 Docker（本機 `psql` 直連）

```bash
psql -h localhost -p 5432 -U postgres -d dashboardmanager \
  -f people-density/output/seed/02_dashboardmanager_components.sql
psql -h localhost -p 5432 -U postgres -d dashboardmanager \
  -f people-density/output/seed/03_map_layers_dashboard.sql
```

---

## 驗證

1. **DB 端**

```sql
-- 組件已註冊
SELECT * FROM public.components       WHERE id = 941;
SELECT * FROM public.component_charts WHERE index = 'metrotaipei_village_population_density';
SELECT * FROM public.component_maps   WHERE index = 'metrotaipei_village_population_density';
SELECT index, city, query_type FROM public.query_charts
 WHERE index = 'metrotaipei_village_population_density';

-- map-layers-* 儀表板已包含 941
SELECT id, index, name, components FROM public.dashboards WHERE id IN (106, 359);
```

2. **前端**：進入任一儀表板 → 切換到「地圖交叉比對」 → 左側「基本圖層 / 圖資資訊」
   應看到「村里人口密度」可勾選；勾選後地圖看似無變化（透明），但點擊任一村里範圍
   會跳出 popup 顯示縣市、鄉鎮市區、村里、人口數、戶數、面積、人口密度（人/km²）等資訊。

---

## 相關文件

- `people-density/基本圖層的設定方法.txt` — 基本圖層機制說明（最初線索來源）
- `people-density/config.txt` — `component_maps` 建議設定
- `component_doc/spec.md` — `chart_config` / `map_config` / `paint` 通用規格
- `component_doc/new_component_and_sql_playbook.md` — 新增組件與灌入 SQL 通用流程
- `component_doc/cross_city_dashboard_pattern.md` — `taipei` / `metrotaipei` 雙寫慣例
