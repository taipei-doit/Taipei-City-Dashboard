# 雙北（跨城市）儀表板與 city 切換作法

> 適用情境：同一組組件（chart）需同時放在「臺北儀表板」與「雙北儀表板」，
> 並讓使用者於組件上的下拉選單即時切換 `taipei` ↔ `metrotaipei`。

本文件以 **`reuse_energy`（再生能源）** 為例，記錄將既有「臺北儀表板」延伸成「雙北儀表板」的完整過程，
作為後續資料集（PM2.5、car-type、…）擴充雙北版本的標準作法。

---

## 1. 總覽

雙北 / 臺北儀表板的關鍵是 **「同一個 `components.id` × 多筆 `query_charts.city`」+「兩個 dashboard 各掛不同 group」**。
使用者點選組件右上角下拉切換城市時，FE 會用 `(component.index, 新 city)` 重新呼叫
`GET /api/v1/component/:id/chart?city={city}`，後端就會回傳對應 city 的 `query_chart` 結果。

```
                    ┌────────────── DashboardView ──────────────┐
                    │  下拉「臺北市 / 雙北」← cityManager        │
                    │  change-city → setComponentData(city)     │
                    └────────────┬──────────────────────────────┘
                                 │
        ┌────────────────────────▼────────────────────────┐
        │ contentStore.cityDashboard.components           │
        │   一個 component.id 對應多筆 city 版本           │
        └────────────────────────┬────────────────────────┘
                                 │ /component/:id/chart?city=...
        ┌────────────────────────▼────────────────────────┐
        │ dashboardmanager.query_charts                   │
        │   PRIMARY KEY (index, city) → 兩筆同 SQL 或不同 │
        └─────────────────────────────────────────────────┘
```

對應到 demo SQL 中既有的雙北範例：

| dashboard       | dashboard.id | dashboards.index            | dashboard_groups.group_id | groups.name |
| --------------- | ------------ | --------------------------- | ------------------------- | ----------- |
| 長照關懷（臺北） | 356          | `ltc_care_tpe`              | 2                         | `taipei`    |
| 長照關懷（雙北） | 355          | `ltc_care_newtpe`           | 3                         | `metrotaipei` |
| 永續環境（臺北） | 905          | `sustainable_env_taipei`    | 2                         | `taipei`    |
| 永續環境（雙北） | 906          | `sustainable_env_metrotaipei` | 3                         | `metrotaipei` |

> ⚠️ **永續環境儀表板**（ID 905/906）由 `component_doc/seed/03_sustainable_env_dashboard.sql` 統一管理，
> 同時包含綠能轉型（車輛：901/902/903）、再生能源（911/912/913/914）、綠建築（921/922）共 9 個組件。
> 原 `green_transition_*`（901/904）與 `renewable_energy_*`（902/903）四個 dashboard 已廢除。

兩個 dashboard 的 `components` 陣列一致，差異全部落在 `query_charts.city`。

---

## 2. 後端三表的 city 雙寫規則

依 `Documentation/back-end-ch/components-db.md` 與 `component-data-apis.md`：

- `components`：每個 `index` **僅一筆**，`name` 建議**不含城市字樣**（如「再生能源裝置容量 - 年趨勢」），
  雙北儀表板顯示同名也合理。
- `component_charts`：每個 `index` 也**僅一筆**（`color`／`types`／`unit`／`categories` 全 city 共用）。
- `query_charts`：**主鍵為 `(index, city)`**，每個 `index` 為每個欲支援的 city 各插一筆。
- `dashboards`：**為「臺北版」「雙北版」各建一筆**，但 `components` 陣列指向相同 component_id。
- `dashboard_groups`：分別把上面兩個 dashboard 掛到 `taipei`(2) / `metrotaipei`(3) 群組。

> ⚠️ 不要為「雙北版本」另開 `components.id`。否則 FE 在切換 city 時找不到同 `index` 的對應資料。

### SQL 撰寫慣例

| city          | SQL 內容                                                                   |
| ------------- | -------------------------------------------------------------------------- |
| `taipei`      | 只查臺北資料（`WHERE city = '台北市'` 或對應臺北專用表）                   |
| `metrotaipei` | 雙北合計（移除 city 過濾，或 `UNION ALL` 併入 `..._tpe` 與 `..._new_tpe`） |
| `newtaipei`   | 視需要補；目前 `cityManager` 預設未啟用                                    |

回傳欄位仍須符合各 `query_type` 的 `x_axis / y_axis / data` 契約（見 `chart-data.md`）。

---

## 3. FE 的城市切換機制

關鍵檔案：

- `Taipei-City-Dashboard-FE/src/dashboardComponent/utilities/cityManager.ts`
- `Taipei-City-Dashboard-FE/src/views/DashboardView.vue`
- `Taipei-City-Dashboard-FE/src/store/contentStore.js`

### 3.1 `cityManager`：定義各儀表板下的可選城市

```ts
// 摘錄
"taipei":      { selectList: ["taipei"],                tagList: ["taipei"] },
"metrotaipei": { selectList: ["metrotaipei", "taipei"], tagList: ["metrotaipei", "taipei"] },
```

雙北儀表板會自動顯示「雙北 / 臺北市」兩個選項；臺北儀表板下選單只有「臺北市」（被 disabled）。

### 3.2 `DashboardView.vue`：把選單塞進 `DashboardComponent`

```html
<DashboardComponent
  :select-btn="true"
  :select-btn-list="cityManager.getSelectList(currentDashboard.city)"
  :active-city="item.city"
  @change-city="(city) => {
    const target = cityDashboard.components.find(d => d.index === item.index && d.city === city);
    if (target) contentStore.setComponentData(idx, target);
  }"
/>
```

### 3.3 `contentStore`

- 後端 `GET /dashboard/{index}` 回傳 `cityDashboard`，內含**所有 city 版本**的同 index 組件。
- 切換時重新呼叫 `GET /component/{id}/chart?city={city}`（即 `query_charts (index, city)` 對應筆）。
- 因此 **DB 內每個 city 都要有 query_charts 才能正常切換**，否則使用者切過去會空白／報錯。

---

## 4. `reuse_energy` 雙北實作步驟（可作模板）

### 4.1 修改清洗腳本

`reuse_energy/clean_reuse_energy.py` 中已新增雙北常數：

```python
SEED_DASHBOARD_ID            = 902
SEED_DASHBOARD_INDEX         = "renewable_energy_taipei"
SEED_TAIPEI_GROUP_ID         = 2

SEED_METROTAIPEI_DASHBOARD_ID    = 903
SEED_METROTAIPEI_DASHBOARD_INDEX = "renewable_energy_metrotaipei"
SEED_METROTAIPEI_GROUP_ID        = 3
```

並在 `build_dashboardmanager_sql()` 中：

1. `components.name` 拿掉「臺北市」字樣（雙北顯示也合理）。
2. `query_charts` 為四個 `index` 各**插兩筆**（`taipei` + `metrotaipei`）。
3. `dashboards` 同時 INSERT `renewable_energy_taipei` 與 `renewable_energy_metrotaipei`，`components` 陣列共用同 4 個 id。
4. `dashboard_groups` 分別掛 `(902, 2)` 與 `(903, 3)`。

### 4.2 雙北合計 SQL 與臺北 SQL 對照

| `index`                              | `query_type` | `taipei` SQL                       | `metrotaipei` SQL              |
| ------------------------------------ | ------------ | ---------------------------------- | ------------------------------ |
| `reuse_energy_capacity_metrotaipei`  | `three_d`    | 同 metrotaipei（本身就是雙北比較） | 同臺北版                       |
| `reuse_energy_mix_taipei`            | `two_d`      | `WHERE city = '台北市'`            | 移除 city 過濾、`SUM` 雙北     |
| `reuse_energy_trend_taipei`          | `time`       | `WHERE city = '台北市'`            | 移除 city 過濾、`SUM` 雙北     |
| `reuse_energy_trend_column_taipei`   | `three_d`    | `WHERE city = '台北市'`            | 移除 city 過濾、`SUM` 雙北     |

### 4.3 重新產生並灌入

```bash
cd Taipei-City-Dashboard
python3 reuse_energy/clean_reuse_energy.py

# 01 已含資料表本身，schema 不變時可不重灌；02 必須重灌
docker exec -i postgres-manager psql -U postgres -d dashboardmanager -v ON_ERROR_STOP=1 \
  < reuse_energy/output/seed/02_dashboardmanager_components.sql
```

### 4.4 驗證

```bash
docker exec -i postgres-manager psql -U postgres -d dashboardmanager -At -c \
  "SELECT d.id, d.index, dg.group_id, g.name
     FROM dashboards d
     JOIN dashboard_groups dg ON d.id = dg.dashboard_id
     JOIN groups g ON dg.group_id = g.id
    WHERE d.id IN (902, 903) ORDER BY d.id;"

docker exec -i postgres-manager psql -U postgres -d dashboardmanager -At -c \
  "SELECT index, city FROM query_charts
    WHERE index LIKE 'reuse_energy%' ORDER BY index, city;"
```

預期輸出：

```
902|renewable_energy_taipei|2|taipei
903|renewable_energy_metrotaipei|3|metrotaipei
reuse_energy_capacity_metrotaipei|metrotaipei
reuse_energy_capacity_metrotaipei|taipei
reuse_energy_mix_taipei|metrotaipei
reuse_energy_mix_taipei|taipei
reuse_energy_trend_column_taipei|metrotaipei
reuse_energy_trend_column_taipei|taipei
reuse_energy_trend_taipei|metrotaipei
reuse_energy_trend_taipei|taipei
```

實際 SQL 檢查（雙北能源占比）：

```bash
docker exec -i postgres-manager psql -U postgres -d dashboardmanager -At -c \
  "SELECT query_chart FROM query_charts
    WHERE index='reuse_energy_mix_taipei' AND city='metrotaipei';" \
  | xargs -I{} docker exec -i postgres-data psql -U postgres -d dashboard -c "{}"
```

### 4.5 `car-type`（綠能轉型）

`car-type/clean_vehicle_data.py` 已與再生能源採相同模式：

- `SEED_DASHBOARD_ID=901` / `green_transition_taipei` → `dashboard_groups (901, 2)`。
- `SEED_METROTAIPEI_DASHBOARD_ID=904` / `green_transition_metrotaipei` → `dashboard_groups (904, 3)`。
- 三個 `index` 各兩筆 `query_charts`：`city=taipei` 時 `region = '臺北市'`；
  `city=metrotaipei` 時 `region IN ('臺北市', '新北市')` 並對同月、同車種、同燃料 **加總** `count`。
- `vehicle_components.json` 輸出 **六筆** mock（臺北 + 雙北，`id` 仍為 901–903）。

```bash
cd car-type && python3 clean_vehicle_data.py && cd ..
docker exec -i postgres-manager psql -U postgres -d dashboardmanager -v ON_ERROR_STOP=1 \
  < car-type/output/seed/02_dashboardmanager_components.sql
```

驗證：

```bash
docker exec -i postgres-manager psql -U postgres -d dashboardmanager -At -c \
  "SELECT id, index FROM dashboards WHERE index LIKE 'green_transition%' ORDER BY id;"
docker exec -i postgres-manager psql -U postgres -d dashboardmanager -At -c \
  "SELECT index, city FROM query_charts WHERE index LIKE 'vehicle_%' ORDER BY index, city;"
```

---

## 5. 為其他資料集擴充雙北的通用 Checklist

1. **資料準備**：確保 `dashboard` DB 同一張事實表中已含**雙北兩市**資料；若僅有臺北，請先補新北來源。
2. **`components`**：把 name 改為城市中性敘述（例：「能源占比」而非「臺北市能源占比」）。
3. **`query_charts`**：為每個 index 撰寫兩份 SQL，一份只查臺北、一份雙北合計，回傳欄位形狀相同。
4. **`dashboards` / `dashboard_groups`**：建立 `xxx_metrotaipei` dashboard、掛到 `group_id = 3`。
5. **idempotent seed**：`02_*.sql` 的 `DELETE` 段落要同時清掉**兩個 dashboard id 與兩個 dashboard index**。
6. **FE 不需改動**：不必修改 `cityManager`／`DashboardView`／`contentStore`；雙北儀表板的下拉與 city 路由已內建。
7. **驗證**：DB 直接執行兩份 SQL 確認形狀；前端切換選單觀察組件能否正確重新渲染、無 404。

---

## 6. 常見錯誤與排雷

| 症狀                                  | 原因                                                              | 解法                                                                  |
| ------------------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------- |
| 切到雙北選單但組件變空白              | `query_charts` 缺 `(index, 'metrotaipei')` 那筆                   | 在 `02_*.sql` 補插                                                    |
| 雙北儀表板側邊找不到該分組            | `dashboard_groups` 沒掛上 `group_id=3`                            | 補 `INSERT INTO dashboard_groups VALUES (903, 3)`                     |
| 切回臺北看到「雙北加總」              | 雙北 SQL 被同時寫進 `taipei` 那筆                                 | 確認 `taipei` 那筆 SQL `WHERE city = '台北市'`                         |
| 兩個 dashboard 共用 components 但內容不同 | 嘗試為「雙北版」另建 `components.id`                              | 不要這麼做。共用同 id，只在 `query_charts.city` 區分                  |
| `INSERT INTO query_charts` 主鍵衝突   | 同 `(index, city)` 已存在                                         | seed 開頭先 `DELETE FROM query_charts WHERE index IN (...)`           |
| 想動「`DonutChart` 與 `TimelineStackedChart` 合併」 | 既有架構 1 component = 1 query_type，不支援           | 改採「兩個獨立元件 + 共同上層敘述」或新增同 `query_type` 的另一視覺   |

---

## 7. 相關文件索引

| 文件                                                      | 說明                                              |
| --------------------------------------------------------- | ------------------------------------------------- |
| `component_doc/spec.md`                                   | 圖表 / 地圖 / 篩選通用規格                        |
| `component_doc/db.md`                                     | 雙 DB 與三表角色                                  |
| `component_doc/new_component_and_sql_playbook.md`         | 新增組件 + 各 query_type 灌入範例                 |
| `component_doc/reuse_energy_components.md`                | 再生能源四圖（含雙北）完整說明                    |
| `component_doc/car_type_components.md`                    | 綠能轉型三圖（含雙北）完整說明                    |
| `Taipei-City-Dashboard-Documentation/.../components-db.md` | `query_charts (index, city)` 主鍵與欄位定義       |
| `Taipei-City-Dashboard-Documentation/.../chart-data.md`   | `chart_data` 三大形狀與 `query_type` 對照         |
| `Taipei-City-Dashboard-FE/src/.../cityManager.ts`         | 各儀表板的城市選單行為                            |
| `Taipei-City-Dashboard-FE/src/views/DashboardView.vue`    | `select-btn-list` / `change-city` 接線            |
