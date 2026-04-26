# Taipei City Dashboard 整合問題清單

產出日期：2026-04-26
產出範圍：FE + BE + DE + DB
分支：`ping/integration_dashboard_1`（剛 cherry-pick 完 PR #3、#5；最近 5 個 merge：`feature/mapping_data` 系列 + `feature/mapping_data (#1227)`）

---

## 🔴 嚴重：FE / BE endpoint 與 shape 不對齊

「捷運無障礙」儀表板 FE 打 4 支 API，**只有 2 支對得上 BE**。本地 dev 因為 `mock/index.js` 攔截所以看不出問題；**production / nginx-served build 會直接 404**。

| FE 期待 path | BE 實作 path | live 測試 (curl) | shape 對齊？ | 結論 |
|---|---|---|---|---|
| `/api/v1/mrt/a11y/alert-count` | `/api/v1/mrt/a11y/alert-count` | 200 | ✅ `[{data:[{x,y}]}]` | OK |
| `/api/v1/mrt/a11y/alert-by-line` | `/api/v1/mrt/a11y/alert-by-line` | 200 | ✅ `{categories,data:[{name,icon,data}]}` | OK（BE 目前 `data:null`，因 DB 只 1 列 alert） |
| `/api/v1/mrt/a11y/alert-by-type` | （無，BE 只有 `/alert-trend-30d`） | **404** | ❌ 概念不同：FE 要按設施類型（電梯/坡道）；BE 給按路線 30 天累計 | 🔴 |
| `/api/v1/mrt/a11y/station-overview` | （無，BE 只有 `/stations`） | **404** | ❌ 概念不同：FE 要 `[{name,type,icon,value}]` legend overview；BE 給 188 列 `[{station,exit_no,lng,lat,...}]` map markers | 🔴 |

實際呼叫位置：
- [MrtAccessibilityView.vue:131-135](Taipei-City-Dashboard-FE/src/views/MrtAccessibilityView.vue#L131-L135)
- [MrtAccessibilityV2View.vue:131-134](Taipei-City-Dashboard-FE/src/views/MrtAccessibilityV2View.vue#L131-L134)
- BE 註冊於 [router.go:212-220](Taipei-City-Dashboard-BE/app/routes/router.go#L212-L220)
- BE 實作 [mrtA11y.go (controller)](Taipei-City-Dashboard-BE/app/controllers/mrtA11y.go) / [mrtA11y.go (model)](Taipei-City-Dashboard-BE/app/models/mrtA11y.go)

→ **建議**：FE 與 BE 雙方對 C3 / C4 的「需求樣板」沒同步，應於本 sprint 內定 contract 收斂（見文末「對齊方案備選」）。

## 🔴 嚴重：FE 重複實作（V1 / V2 並存）

[MrtAccessibilityView.vue](Taipei-City-Dashboard-FE/src/views/MrtAccessibilityView.vue) 與 [MrtAccessibilityV2View.vue](Taipei-City-Dashboard-FE/src/views/MrtAccessibilityV2View.vue) 內容幾乎相同（fetchAll、4 個 c1~c4 component、layer 設定都一樣）。Sidebar 同時顯示兩個入口（[SideBar.vue:160,170](Taipei-City-Dashboard-FE/src/components/utilities/bars/SideBar.vue#L160)），路由 `/mrt-a11y` 與 `/mrt-a11y-v2` 都註冊（[router/index.js:65-87](Taipei-City-Dashboard-FE/src/router/index.js#L65-L87)）。

→ **建議**：擇一保留並下架另一支，避免 BE 對齊改動要做兩次。

---

## 🟡 DB 表沒人用（孤兒表）

`dashboard` DB 共 16 張業務表，BE 只 query 了 a11y 三張，其餘皆無 model / controller 可呼叫到：

| 表名 | 行數 | BE 有 query？ | 來源 DAG |
|---|---|---|---|
| `mrtp_a11y_alert` | 1 | ✅ models/mrtA11y.go:42 / 63 / 118 | `proj_city_dashboard_mrt_a11y_alert` |
| `mrtp_a11y_alert_history` | 14 | ✅ models/mrtA11y.go:86 | 同上（with `load_behavior=current+history`） |
| `mrtp_a11y_elevator` | 188 | ✅ models/mrtA11y.go:115 | `proj_city_dashboard_mrt_a11y_elevator` |
| `bike_network_tpe` / `_new_tpe` | n/a | ❌ | — |
| `bike_network_new_tpe` | n/a | ❌ | — |
| `bus_info_tpe` / `_new_tpe` | n/a | ❌ | — |
| `tran_ubike_realtime` / `_new_tpe` | n/a | ❌ | — |
| `city_age_distribution_taipei` / `_newtaipei` | n/a | ❌ | — |
| `population_age_distribution_tpe` / `_new_tpe` | n/a | ❌ | — |
| `dependency_ratio_and_aging_index_tpe` / `_new_tpe` | n/a | ❌ | — |
| `employment_age_structure_tpe` / `_new_tpe` | n/a | ❌ | — |

注意：dashboard 系統其餘 chart 是走 `dashboardmanager.query_charts.query_chart` 動態 SQL（generic 路由 `/component/:id/chart`），所以 BE Go 程式中沒 hard-code 的 model 不一定代表「無人用」— 但本 audit 範圍是 a11y 儀表板專屬流，這些表都不在這條鏈上。

→ **建議**：若這些表是其他儀表板（人口、單車、公車）會用到，要在文件記錄綁定關係，避免被當成可清理。

## 🟡 FE 殘留靜態資料 / mock

| 路徑 | 內容 | 現狀 |
|---|---|---|
| [AccessibilityRouteView.vue:24-35](Taipei-City-Dashboard-FE/src/views/AccessibilityRouteView.vue#L24-L35) | `slopeCounts` 12 區寫死數字（北投區: 1620 …） | mock，註解寫「BE 將以同樣 schema 回傳」 |
| [AccessibilityRouteView.vue:37-40](Taipei-City-Dashboard-FE/src/views/AccessibilityRouteView.vue#L37-L40) | `workCounts` 12 區寫死數字 | mock |
| [AccessibilityRouteView.vue:51](Taipei-City-Dashboard-FE/src/views/AccessibilityRouteView.vue#L51) | `source: "示範資料｜BE 將以行政區彙總回傳"` | 字串明示 demo |
| [AccessibilityRouteView.vue:70](Taipei-City-Dashboard-FE/src/views/AccessibilityRouteView.vue#L70) | `source: "示範資料｜BE 將以每 10 分鐘輪詢更新"` | 字串明示 demo |
| [AccessibilityRouteView.vue:92-101](Taipei-City-Dashboard-FE/src/views/AccessibilityRouteView.vue#L92-L101) | `slopeMockGeoJson` 7 features 寫死 | mock GeoJSON |
| [AccessibilityRouteView.vue:105-113](Taipei-City-Dashboard-FE/src/views/AccessibilityRouteView.vue#L105-L113) | `workMockGeoJson` 4 features 寫死 | mock GeoJSON |
| [public/mapData/mrt_station_demo.geojson](Taipei-City-Dashboard-FE/public/mapData/mrt_station_demo.geojson) | demo 站點 GeoJSON（板南/淡水信義線數站） | 由 V1 / V2 view 載入；正式應改用 BE `/stations` 動態產生 |
| [mock/index.js](Taipei-City-Dashboard-FE/mock/index.js) | 4 條 routes mapping，2 條 BE 已實作（alert-count, alert-by-line） | 兩條可移除；剩兩條因 BE 沒對應仍需保留 |
| [mock/mrt-a11y/alert-count.json](Taipei-City-Dashboard-FE/mock/mrt-a11y/alert-count.json) | 死檔（BE 已實作） | 可刪 |
| [mock/mrt-a11y/alert-by-line.json](Taipei-City-Dashboard-FE/mock/mrt-a11y/alert-by-line.json) | 死檔（BE 已實作） | 可刪 |

→ AccessibilityRouteView 整支是 demo（無對應 BE / DAG / DB），與已對齊好流的 MrtAccessibilityView 不同層級。

## 🟡 DE DAG 與下游對齊

| DAG 全名（Airflow ID） | 寫入表 | BE 用？ | FE 用？ | 最近 dag_run |
|---|---|---|---|---|
| `proj_city_dashboard_mrt_a11y_alert` | `mrtp_a11y_alert` (+ history) | ✅ | ✅ (alert-count, alert-by-line, alert-trend-30d, stations 都依賴) | 待查（`airflow dags list-runs -d proj_city_dashboard_mrt_a11y_alert` 沒有近期紀錄輸出） |
| `proj_city_dashboard_mrt_a11y_elevator` | `mrtp_a11y_elevator` | ✅ (stations endpoint LEFT JOIN) | ✅ | 待查 |

提醒：Airflow 內 DAG ID 都帶 `proj_city_dashboard_` prefix，**裸名 `mrt_a11y_alert` 不存在**。`run-de-dag` skill 文件提到的裸名要在 trigger 時自動 prefix，否則會 `does not exist in 'dag' table`。

DB 行數異常少（alert=1、history=14、elevator=188）— 188 elevator 算正常（北捷+環狀＋部分新北約 200 站），但 alert=1 / history=14 顯示 DAG 跑過的次數很少。建議跑 `run-de-dag` 把資料補新。

## 🟡 規劃但未實作

| 位置 | 註解原文 | 解讀 |
|---|---|---|
| [AccessibilityRouteView.vue:24](Taipei-City-Dashboard-FE/src/views/AccessibilityRouteView.vue#L24) | `Mock chart data — BE 將以同樣 schema 回傳 (district -> count)` | BE 完全沒實作 district-level 斜坡道彙總 |
| [AccessibilityRouteView.vue:51](Taipei-City-Dashboard-FE/src/views/AccessibilityRouteView.vue#L51) | `示範資料｜BE 將以行政區彙總回傳` | 同上 |
| [AccessibilityRouteView.vue:70](Taipei-City-Dashboard-FE/src/views/AccessibilityRouteView.vue#L70) | `示範資料｜BE 將以每 10 分鐘輪詢更新` | 「今日施工通報」endpoint 也未實作 |
| [models/user.go:234](Taipei-City-Dashboard-BE/app/models/user.go#L234) | `TODO: delete user's view point` | user 刪除時沒清 view_point |
| [controllers/componentConfig.go:44](Taipei-City-Dashboard-BE/app/controllers/componentConfig.go#L44) | `FIXME:` | 未說明的 FIXME |

---

## 🟢 服務狀態

| 服務 | URL/Port | 狀態 | 備註 |
|---|---|---|---|
| dashboard-be | http://localhost:8088 | ✅ Up 41m | a11y 4 個路由僅 2 個對齊 FE |
| dashboard-fe | http://localhost:8080 | ⚠️ Up 27m，但 `curl /` 連不上（HTTP 000） | 容器在跑，但 nginx 對外路徑可能沒接好 |
| nginx | http://localhost:80 | ❌ HTTP 502 Bad Gateway | upstream 沒接好 |
| airflow-webserver | http://localhost:8081 | ⚠️ root 404；`/login` 回 "Apache Airflow is not at this location" | UI 不在預期位置，或 `WEBSERVER_BASE_URL` 設了非 `/` 的 prefix |
| airflow-scheduler/worker × 4 | — | ✅ healthy 14h | DAG 載入無 import error |
| postgres-data | 5432 (container only) | ✅ Up 15h | dashboard DB |
| postgres-manager | 0.0.0.0:5432 | ✅ Up 15h | dashboardmanager DB |
| pgadmin | http://localhost:8889 | ✅ Up 15h | 未驗 |
| redis | 6379 | ✅ Up 15h | — |

**🟢 設計層面（次要 / 清債）**

- FE 沒有 service / API client layer：4 條 axios.get 在 view 內裸 import，重複出現於 V1 / V2，難集中改。建議抽出 `src/services/mrtA11y.js`。
- BE `models/mrtA11y.go` 同一個 `mrtp_a11y_alert WHERE status='active'` query 重複出現於 alert-count / alert-by-line / stations subquery — 可抽 helper。
- `mock/index.js` 的 mapping 應只在 BE 真的沒實作時保留；目前留了 2 條已實作的死 mapping，dev 環境會吃 mock 而不知道 BE 已 OK。

---

## 建議優先順序

1. **🔴 收斂 a11y C3 / C4 的 contract**（決定 alert-by-type vs alert-trend-30d 留哪個、station-overview vs stations 留哪個 / 還是兩邊各一個）。這是 demo 阻塞點。
2. **🔴 V1 / V2 view 二擇一**，否則 contract 收斂後要改兩次。
3. **🟡 把已實作的 mock 條目從 `mock/index.js` 移除**（alert-count, alert-by-line），讓 dev 環境直接打 BE，能更早發現 contract 漂移。
4. **🟡 跑一輪 DAG**（`proj_city_dashboard_mrt_a11y_alert` + `_elevator`）把 DB 充實，避免 demo 看到空 chart。
5. **🟡 修 nginx 502 + 確認 FE 容器對外**，否則 production demo 連得到 BE 連不到 FE。
6. **🟢 AccessibilityRouteView demo 流**：明示時程是「下個 sprint」還是「Q3」，避免被當成已實作；如果短期不做，sidebar 可暫時藏起來。

---

## 對齊方案備選（給 a11y C3 / C4 mismatch）

### 選項 A：BE 補出 FE 期待的兩支（保留現有兩支）

新增 BE：
- `GET /api/v1/mrt/a11y/alert-by-type` → 從 `mrtp_a11y_alert WHERE status='active'` group by `facility_type`（要先確認 alert 表有 `facility_type` 欄位；目前看 schema 只有 elevator 表有）。可能要 JOIN elevator 拿 facility_type。
- `GET /api/v1/mrt/a11y/station-overview` → 從 `stations` 結果聚合成 `[{name:"異常",type:"alert",value:N}, {name:"正常",type:"normal",value:M}]`。

工作量：**0.5–1 天**（含 join / 測試 / FE 移除 mock）。

### 選項 B：FE 改打 BE 既有路由（最少 BE 改動）

- C3 改打 `alert-trend-30d`，但語意改成「近 30 天各路線公告數」（不是按設施類型），這需重設計 chart。
- C4 改打 `stations`，FE 在前端把 188 列攤平成 `{alert: N, normal: M}` 統計。

工作量：**1–2 小時**，但 C3 在儀表板上的意義從「目前異常分布」變成「歷史趨勢」，需 PM 確認。

### 選項 C：兩邊都動，重設計 contract（推薦，給時間夠的話）

- BE 加 `/alert-by-type`（仿 `alert-by-line`），刪掉 `alert-trend-30d` 或保留作為加值。
- FE 把 `/station-overview` 改名 / shape 對齊 BE `/stations`，並讓 C4 變成同時顯示 legend + 地圖標記（兩者本就同源）。
- 移除 `mock/mrt-a11y/*` 已實作的兩支 JSON，剩兩支隨 BE 上線一起刪。

工作量：**1 天**（FE / BE 各半天 + 整合測試）。
