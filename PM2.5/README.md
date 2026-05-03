# 即時 PM2.5 空氣品質地圖組件

新增雙北「即時 PM2.5 空氣品質」地圖組件。
資料來源為民生公共物聯網的 OGC SensorThings API（環境部空品微型感測器），
資料抓取邏輯與 GeoJSON 規格請參考：

- `PM2.5/doc/data_collect.txt` — 第 1~4 點資料源 / 抓取流程 / Mapbox 配置建議
- `PM2.5/fetch_pm25.py` — 實際抓取與輸出 GeoJSON 的 Python 腳本

> 設計選擇：依 `component_doc/spec.md`「Circle」段落，本組件採用
> **`type=circle` + `icon='heatmap'`** 的組合，由前端
> `/src/assets/configs/mapbox/mapConfig.js` 內 `maplayerCommonPaint['circle-heatmap']`
> 自動套用 `circle-radius` / `circle-blur` / `circle-opacity` 隨 zoom 變化的預設樣式
> ──地圖拉遠時點位模糊成「熱點圖」效果，放大時還原為單點圓圈。
> 這是專案內慣用的熱點圖實作（`backup_all_components.json` 中
> 交通事故 / 派工類別等也都用這個組合）。

---

## 設計重點

| 欄位                  | 值                                                                                                                |
| --------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `components.id`       | `942`                                                                                                             |
| `components.index`    | `pm25_realtime`                                                                                                   |
| `components.name`     | `即時 PM2.5 空氣品質`                                                                                             |
| 圖表類型              | `MapLegend`（顯示 EPA AQI 6 段標準色圖例）                                                                        |
| 地圖類型              | `circle`（點圖）                                                                                                  |
| 地圖變化              | `icon = 'heatmap'`（套用前端 `circle-heatmap` 預設樣式：縮小→模糊熱點 / 放大→單點）                               |
| `paint`               | `{"circle-color": ["get", "aqi_color"]}`（直接讀 GeoJSON feature 的 EPA 標準色）                                  |
| `map_filter`          | `byParam(aqi_label_zh)`（點圖例可篩選對應 AQI 等級的測站）                                                        |
| `property`（popup）   | `station / city / township / area / pm25 / aqi / aqi_label_zh / authority / localTime`                            |
| `query_type`          | `map_legend`                                                                                                      |
| `city`                | 雙寫 `taipei` 與 `metrotaipei`                                                                                    |
| 掛載到的儀表板        | `dashboards.id = 905` (`sustainable_env_taipei`)、`dashboards.id = 906` (`sustainable_env_metrotaipei`) — 永續環境 |

### EPA AQI 顏色對照（與 `fetch_pm25.py` 內的 `AQI_LEVELS` 一致）

| AQI 上界 | 英文等級                       | 中文等級             | HEX       |
| -------- | ------------------------------ | -------------------- | --------- |
| 50       | Good                           | 良好                 | `#00E400` |
| 100      | Moderate                       | 普通                 | `#FFFF00` |
| 150      | Unhealthy for Sensitive Groups | 對敏感族群不健康     | `#FF7E00` |
| 200      | Unhealthy                      | 對所有族群不健康     | `#FF0000` |
| 300      | Very Unhealthy                 | 非常不健康           | `#8F3F97` |
| 500      | Hazardous                      | 危害                 | `#7E0023` |

`component_charts.color` 陣列順序、`query_charts.query_chart` 的 `VALUES` 順序、
以及 `aqi_label_zh` 在 GeoJSON feature 中的字串值都一致，確保
**圖例顏色 = 地圖點顏色**。

---

## 檔案結構

```
PM2.5/
├── README.md                              ← 本檔
├── doc/
│   ├── data_collect.txt                   ← 資料源 / 抓取流程說明（內含 Mapbox 配置建議）
│   └── problem_to_fix.txt
├── fetch_pm25.py                          ← Python 抓取腳本（輸出 GeoJSON / CSV）
├── requirements.txt
├── test/
│   ├── heatmap_pm25.geojson
│   ├── out.geojson
│   └── test.py
└── output/
    └── seed/
        ├── 02_dashboardmanager_components.sql   ← 註冊組件
        └── 03_sustainable_env_dashboard_addon.sql ← 掛入 905/906 永續環境儀表板
```

GeoJSON 已存於前端：

```
Taipei-City-Dashboard-FE/public/mapData/pm25_realtime.geojson
```

> 慣例：`component_maps.index` 必須與 `public/mapData/{index}.geojson` 檔名一致。
> 若 `fetch_pm25.py` 重跑產生新檔，請覆寫此路徑下的 `pm25_realtime.geojson`。

---

## 灌入順序（Docker；對應 `docker/.env` 預設容器名）

本組件**不需要 `dashboard` DB 事實表**（資料直接來自前端讀取 GeoJSON），
僅需在 `dashboardmanager` 註冊組件並掛上儀表板：

```bash
# 1. 註冊組件（components / component_charts / component_maps / query_charts）
docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
  < PM2.5/output/seed/02_dashboardmanager_components.sql

# 2. 將組件掛入「永續環境」儀表板（905 / 906）
docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
  < PM2.5/output/seed/03_sustainable_env_dashboard_addon.sql
```

兩支 SQL 皆**冪等**（重跑不會重覆插入；Step 2 用 `DISTINCT` 合併陣列）。

### 非 Docker（本機 `psql` 直連）

```bash
psql -h localhost -p 5432 -U postgres -d dashboardmanager \
  -f PM2.5/output/seed/02_dashboardmanager_components.sql
psql -h localhost -p 5432 -U postgres -d dashboardmanager \
  -f PM2.5/output/seed/03_sustainable_env_dashboard_addon.sql
```

---

## 驗證

1. **DB 端**

```sql
SELECT * FROM public.components       WHERE id = 942;
SELECT * FROM public.component_charts WHERE index = 'pm25_realtime';
SELECT * FROM public.component_maps   WHERE index = 'pm25_realtime';
SELECT index, city, query_type, map_filter
  FROM public.query_charts
 WHERE index = 'pm25_realtime';

-- 永續環境儀表板已包含 942
SELECT id, index, name, components FROM public.dashboards WHERE id IN (905, 906);
```

2. **前端**

   - 進入「永續環境」儀表板（臺北 / 雙北皆可），找到「即時 PM2.5 空氣品質」組件 →
     地圖上即出現雙北測站熱點：拉遠時模糊成熱力圖、放大時還原為單點圓圈，顏色依
     EPA AQI 等級分佈。
   - 點擊任一測站圓點 → popup 顯示測站名稱、縣市、鄉鎮市區、區域、PM2.5、AQI、
     AQI 等級、資料機關、觀測時間。
   - 點擊右側 `MapLegend` 任一 AQI 等級 → 地圖只保留該等級的測站（`map_filter`
     `byParam` 對 `aqi_label_zh`）；再點一次取消篩選。

---

## 進階：定時更新 GeoJSON

`fetch_pm25.py` 可放入 cron / supervisor 定時執行，輸出覆寫
`Taipei-City-Dashboard-FE/public/mapData/pm25_realtime.geojson`，
即可獲得「每 5 分鐘更新」的近即時 PM2.5 熱點圖
（與 `query_charts.update_freq = 5 minute` 對齊）。

範例 crontab：

```cron
*/5 * * * * cd /opt/Taipei-City-Dashboard && \
  python3 PM2.5/fetch_pm25.py \
  --out Taipei-City-Dashboard-FE/public/mapData/pm25_realtime.geojson
```

> 實際旗標請以 `python3 PM2.5/fetch_pm25.py --help` 為準。

---

## 相關文件

- `PM2.5/doc/data_collect.txt` — 第 1~4 點資料源、抓取流程、Mapbox heatmap 配置建議
- `component_doc/spec.md` — `chart_config` / `map_config` / `paint`、`Circle` 與 `heatmap` icon 變化說明
- `component_doc/new_component_and_sql_playbook.md` — 新增組件與灌入 SQL 通用流程
- `component_doc/cross_city_dashboard_pattern.md` — `taipei` / `metrotaipei` 雙寫慣例
- `Taipei-City-Dashboard-FE/src/assets/configs/mapbox/mapConfig.js` — `maplayerCommonPaint['circle-heatmap']` 預設樣式定義
- `Taipei-City-Dashboard-FE/src/dashboardComponent/components/MapLegend.vue` — `MapLegend` 圖例渲染邏輯（type='circle' → 圓點）
