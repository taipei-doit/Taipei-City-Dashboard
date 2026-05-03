# 新增組件與資料灌入作業手冊

本文件分兩段：**（一）新增組件的通用完整步驟**；**（二）目前專案中各 `query_type`／圖表類型與對應的 SQL 灌入指令**。  
詳細欄位與圖表契約仍以 `spec.md`、`db.md` 及 [Taipei-City-Dashboard-Documentation](https://github.com/tpe-doit/Taipei-City-Dashboard-Documentation) 之 `chart-data.md`、`component-data-apis.md` 為準。

---

## （一）新增組件的通用完整步驟

### 1. 對齊規範與圖表契約

- 閱讀 `component_doc/spec.md`：`chart_config`（`color`、`types`、`unit`、`categories`）、圖表英文名（PascalCase）。
- 確認目標圖表在 FE 對應的 **`query_type`** 與 **`chart_data` 形狀**（見本文件第二節對照表）。
- 後端 SQL 回傳欄位須為 **`x_axis`、`y_axis`（視類型可為 NULL）、`data`**，編譯規則見 Documentation 之 `component-data-apis.md`。

### 2. 評估原始資料是否足夠

- 若無法對應到所需的維度（例如 `time` 缺時間欄、`three_d` 缺類別軸），應**先補資料或改圖表類型**，不要硬塞不符合契約的 JSON。

### 3. 撰寫清洗管線（建議與 car-type / reuse_energy 同模式）

- 在專案子目錄放來源檔（CSV 等）與 `doc/data_collect.txt`（清洗規則說明）。
- 以一支 Python 腳本（例如 `clean_xxx_data.py`）完成：
  - 輸出 **長表**（供 `dashboard` DB 建表／`INSERT` 或 `\copy`）。
  - 輸出 **`*_components.json`**（含完整組件欄位與靜態 `chart_data`，供 FE mock）。
  - 輸出 **`output/seed/01_dashboard_data.sql`**：`DROP/CREATE` 資料表 + `INSERT` 全部列（或改為你們慣用的 migration）。
  - 輸出 **`output/seed/02_dashboardmanager_components.sql`**：`components`、`component_charts`、`query_charts`。**儀表板歸屬（`dashboards`、`dashboard_groups`）請放到獨立的 seed 檔**（如 `component_doc/seed/03_sustainable_env_dashboard.sql`），以利多資料集共用同一個側邊欄 Dashboard。
- 腳本內固定 **`components.id`、`dashboards.id`、`index`**，**避免與既有 demo 或他組資料集衝突**（可查 `db-sample-data` 或現有 seed）。

### 4. 填齊組件中繼資料

- `query_charts`：`city`（如 `taipei` / `metrotaipei` / `newtaipei`）、`time_from`（靜態圖常用 `static`）、`source`、`short_desc`、`long_desc`、`use_case`、`links`、`contributors`。
- 無地圖時：`map_config_ids` 為 `'{}'`，`map_filter`、`history_config` 可為 `NULL`（與現有靜態圖一致）。
- **若需同時上架到「臺北儀表板」與「雙北儀表板」**：請參考
  [`cross_city_dashboard_pattern.md`](./cross_city_dashboard_pattern.md)，重點為
  「同一個 `components.id` × 多筆 `query_charts.city` × 兩個 dashboard 各掛不同 group」。

### 5. 本地驗證（建議）

- 在 `dashboard` DB 直接執行 `query_charts.query_chart` 內 SQL，確認列數與欄位名正確。
- FE：將 `*_components.json` 餵給 `DashboardComponent.vue`，確認圖表渲染無誤後再依賴 API。

### 6. 灌入兩個資料庫

- **`dashboard`（容器/服務：常為 `postgres-data`）**：先執行 **`01_dashboard_data.sql`**，建立/更新事實表與資料。
- **`dashboardmanager`（常為 `postgres-manager`）**：再執行 **`02_dashboardmanager_components.sql`**，註冊組件與查詢；若 `query_chart` 引用新表，**順序必須先 01 後 02**。

### 7. 維運

- 來源檔更新後：重跑清洗腳本 → 重灌 **`01`**（會覆寫該表資料時注意 `DROP`）→ 若 schema／index 未變，**`02` 可不必重灌**；若 `query_chart` 或 `id` 有變，需重灌 **`02`**。

---

## （二）各圖的資料類型與灌入 SQL 指令

### 2.1 `query_type`／圖表對照（本 repo 已落地的範例）

| `query_type`  | 主要圖表類型（`chart_config.types[0]`） | `chart_data` 重點（靜態 mock）                                                                | 範例 `index`（car-type）    | 範例 `index`（reuse_energy）                                                        |
| ------------- | --------------------------------------- | --------------------------------------------------------------------------------------------- | --------------------------- | ----------------------------------------------------------------------------------- |
| **`three_d`** | `ColumnChart`（堆疊縱向長條）           | `chart_config.categories` 為 X 類別；`chart_data` 為多個 `{ "name", "data": [數字, …] }` 序列 | `vehicle_type_count_taipei` | `reuse_energy_capacity_metrotaipei`、`reuse_energy_trend_column_taipei`（X 為年度） |
| **`two_d`**   | `DonutChart`（常搭配 `BarChart`）       | 單一物件：`{ "name": "", "data": [ { "x", "y" }, … ] }`                                       | `vehicle_fuel_mix_taipei`   | `reuse_energy_mix_taipei`                                                           |
| **`time`**    | `TimelineStackedChart`                  | 陣列：`[ { "name", "data": [ { "x": ISO 時間+時區, "y" }, … ] }, … ]`                         | `vehicle_fuel_trend_taipei` | `reuse_energy_trend_taipei`                                                         |

更細的 JSON 範例見 `component_doc/car_type_components.md`、`component_doc/reuse_energy_components.md`。

### 2.2 `dashboard` 事實表（供對照）

| 資料集       | 資料庫      | 資料表                                |
| ------------ | ----------- | ------------------------------------- |
| car-type     | `dashboard` | `public.vehicle_registration_monthly` |
| reuse_energy | `dashboard` | `public.reuse_energy_capacity`        |

### 2.3 灌入 SQL：Docker（與 `docker/.env` 預設一致）

**前置條件**：本機已啟動 Compose，且容器名稱為 **`postgres-data`**（dashboard）、**`postgres-manager`**（dashboardmanager）。  
下列指令假設**目前工作目錄為專案根目錄** `Taipei-City-Dashboard/`（請依實際 clone 路徑調整）。

#### car-type（車輛新領牌三圖）

`02_dashboardmanager_components.sql` 管理三個組件（901/902/903）的 `components`、`component_charts`、`query_charts`，各有 `taipei`／`metrotaipei` 兩筆。**不含 dashboard**（由 `03_sustainable_env_dashboard.sql` 管理）。

```bash
docker exec -i postgres-data psql -U postgres -d dashboard \
  < car-type/output/seed/01_dashboard_data.sql

docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
  < car-type/output/seed/02_dashboardmanager_components.sql
```

#### reuse_energy（再生能源四圖）

同上，`02_*.sql` 僅管理四個組件（911/912/913/914），**不含 dashboard**。

```bash
docker exec -i postgres-data psql -U postgres -d dashboard \
  < reuse_energy/output/seed/01_dashboard_data.sql

docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
  < reuse_energy/output/seed/02_dashboardmanager_components.sql
```

#### 永續環境儀表板（合併 car-type + reuse_energy）

建立 / 重建「永續環境」側邊欄（ID 905/906，包含全部 7 個組件）：

```bash
docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
  < component_doc/seed/03_sustainable_env_dashboard.sql
```

#### 完整首次灌入順序（資料 → 組件 → 儀表板）

```bash
# 1. 事實表資料
docker exec -i postgres-data psql -U postgres -d dashboard \
  < car-type/output/seed/01_dashboard_data.sql
docker exec -i postgres-data psql -U postgres -d dashboard \
  < reuse_energy/output/seed/01_dashboard_data.sql

# 2. 組件與查詢設定
docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
  < car-type/output/seed/02_dashboardmanager_components.sql
docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
  < reuse_energy/output/seed/02_dashboardmanager_components.sql

# 3. 永續環境儀表板（合併側邊欄）
docker exec -i postgres-manager psql -U postgres -d dashboardmanager \
  < component_doc/seed/03_sustainable_env_dashboard.sql
```

### 2.4 非 Docker（本機 `psql` 直連）

將 host／port／帳密換成你的環境（`docker/.env` 中 `DB_*`）：

```bash
psql -h localhost -p 5432 -U postgres -d dashboard \
  -f car-type/output/seed/01_dashboard_data.sql
psql -h localhost -p 5432 -U postgres -d dashboardmanager \
  -f car-type/output/seed/02_dashboardmanager_components.sql
```

（`reuse_energy` 同理，將檔案路徑改為 `reuse_energy/output/seed/…`。）

### 2.5 重跑清洗後再灌入

資料來源更新時，請在對應子目錄執行腳本後再執行上一節的 `docker exec`：

```bash
cd car-type && python3 clean_vehicle_data.py && cd ..
cd reuse_energy && python3 clean_reuse_energy.py && cd ..
```

---

## 相關文件索引

| 文件                                                  | 說明                                  |
| ----------------------------------------------------- | ------------------------------------- |
| `component_doc/spec.md`                               | 圖表／地圖／篩選通用規格              |
| `component_doc/db.md`                                 | 雙 DB 角色與表意圖                    |
| `component_doc/car_type_components.md`                | 車輛三圖完整說明                      |
| `component_doc/reuse_energy_components.md`            | 再生能源四圖完整說明                  |
| `component_doc/cross_city_dashboard_pattern.md`       | 雙北儀表板與 city 切換通用作法        |
| `component_doc/seed/03_sustainable_env_dashboard.sql` | 永續環境合併儀表板 seed（可重複執行） |
| `car-type/doc/frontend_integration.md`                | car-type 前端整合精簡版               |
| `reuse_energy/doc/frontend_integration.md`            | reuse_energy 前端整合精簡版           |
