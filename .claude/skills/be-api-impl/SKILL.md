---
name: be-api-impl
description: >
  給定一份 DE 實作規劃（含 DB schema）＋可行性評估報告中的 component 清單，完整走完後端實作四步驟：
  ① 開出 API contract（endpoint × request × response schema）
  ② 在本地 PostgreSQL 建表並塞假資料
  ③ 實作 Go API（models / controllers / routes，對齊 Taipei-City-Dashboard-BE 既有型別）
  ④ 撰寫 unit test 並跑通回報。

  觸發情境：使用者說「實作 api」「幫我寫 backend」「cook 這個儀表板的 BE」「把 DE plan 轉成 API」「根據 schema 寫 controller」「開 api contract」「塞假資料再實作」「生 swagger yaml」；或已有 DE 實作規劃檔（`*_DE實作規劃*.md`）、可行性報告（`題目評估報告/*.md`）而使用者問「BE 這邊要做什麼」。
  即使使用者沒有明講四個步驟，只要背景是 Taipei-City-Dashboard-BE（Go + Gin + GORM + PostgreSQL）且需要實作資料 API，就觸發這個 skill。
---

# be-api-impl

從 DE plan 到可跑的 Go API + unit test，完整四步走完不省略。

## 為什麼需要這個 skill

Taipei-City-Dashboard-BE 有固定的架構慣例（`DBDashboard` 全域連線、既有 chart 資料型別、Gin router 分組、`query_charts` 表）。如果不熟這個架構，容易：
- 重造 `TwoDimensionalDataOutput` 之類已有的型別
- 把 SQL 硬寫在 controller 而非 model 層
- 不知道 `DBDashboard` vs `DBManager` 的分工（資料庫 vs 設定庫）
- 測試連不上 DB 因為不知道用哪個 local PG 帳號

這個 skill 把四步驟固定成可重複執行的流程，讓每次 BE 實作都有一致的產出品質。

---

## 事前準備：收集兩份輸入

開始前先確認使用者提供（或能指向）：

1. **DE 實作規劃**（`*_DE實作規劃_儀表板*.md`）：含 PostgreSQL table schema（欄位名、型別）、DAG 排程、load_behavior。
2. **可行性評估報告**（`題目評估報告/*/NN_*.md`）中對應儀表板的 component 清單：含每個 component 的 chart type（`two_d` / `three_d` / `percent` / `map_legend`）與 SQL 提示。

這兩份是這個 skill 的「schema 與需求」來源，少一份就問使用者要。

---

## Step 1：開 API Contract

### 1a. 對齊現有 chart 型別

Taipei-City-Dashboard-BE 有四種標準 chart 資料型別，對應前端渲染元件。從 `app/models/componentData.go` 確認：

| query_type | Go 輸出型別 | FE 元件 | 回應結構 |
|---|---|---|---|
| `two_d` | `[]TwoDimensionalDataOutput` | 數字卡片、單軸折線 | `{"data":[{"data":[{"x":"…","y":3}]}]}` |
| `three_d` | `[]ThreeDimensionalDataOutput` + `categories []string` | 長條圖 | `{"data":[{"name":"…","icon":"","data":[3,2]}],"categories":[…]}` |
| `percent` | 同 `three_d` | 圓餅圖 | 同上，`data[i].data` 固定長度 1 |
| `map_legend` | `[]MapLegendData` | 地圖圖例 | `{"data":[{"name":"…","type":"…","icon":"…","value":4}]}` |

**原則**：新 component 優先沿用這四種型別，不要自訂新 struct——除非資料結構完全不符。

### 1b. 對應每個 component 決定 endpoint

以路由群組 `/api/v1/<domain>/<subdomain>/` 組織，例如：
- `/api/v1/mrt/a11y/alert-count` → two_d
- `/api/v1/mrt/a11y/alert-by-line` → three_d
- `/api/v1/mrt/a11y/alert-by-type` → percent
- `/api/v1/mrt/a11y/station-overview` → map_legend

所有 endpoint：GET，無必填參數，無 request body。

### 1c. 寫出 API Contract 表格

產出格式：

```
| Component | Endpoint | Method | Response type | FE 渲染 |
| SQL 摘要（1–2 行） |
```

並針對每個 endpoint 說明回應中每個欄位的語意（`x` 是什麼、`y` 是什麼、`type` 允許值為何）。

---

## Step 2：建表 + 塞假資料

### 2a. 找到本地 PostgreSQL

Taipei-City-Dashboard 的本地開發有兩個可能：

1. **Homebrew local PG**（通常在 port 5432，user = OS 目前使用者，database = `dashboard`）
2. **Docker postgres-data 容器**（`docker exec postgres-data psql -U postgres -d dashboard`，通常無 host-side port mapping）

先 `psql -h 127.0.0.1 -p 5432 -l` 確認哪個可用。兩個都用時，**優先用本地 PG**（因為 Go 測試從 host 跑，容器內的 PG 不一定能直接連）。

### 2b. 建表

嚴格對齊 DE plan 的 schema。注意：
- 時間欄位用 `timestamptz`（不是 `timestamp`）
- 有地理資訊的欄位用 `geometry(Point, 4326)`（需要 PostGIS）
- 加必要 index（`status`、`station` 這類 WHERE 常用欄位）

```sql
-- 範例格式
CREATE TABLE IF NOT EXISTS <table_name> (
    <col> <type>,
    ...
);
CREATE INDEX IF NOT EXISTS <idx_name> ON <table_name>(<col>);
```

如果 DB 沒有 PostGIS extension，先執行 `CREATE EXTENSION IF NOT EXISTS postgis;`。

### 2c. 塞假資料

假資料的設計原則：
- **覆蓋所有分支**：每個 component 的 WHERE 條件（如 `status = 'active'`、`status = 'closed'`）都要有資料
- **數字要可驗證**：例如 `status = 'active'` 的筆數要是一個你記得住的整數，測試才能 assert
- **台灣語境**：車站名、路線名、設備類型用真實中文名稱（不要 `foo`、`bar`）
- **筆數最小化**：夠跑測試就好，不需要幾百筆

塞完後執行 `SELECT COUNT(*) GROUP BY status` 類的查詢確認數字對。

---

## Step 3：實作 Go API

### 3a. 新增 model 檔 `app/models/<domain>.go`

```go
package models

// 1. 只定義 DB 查詢需要的 raw row struct（不需重定義 TwoDimensionalData 等已有型別）
type MrtA11yAlertByLine struct {
    Xaxis string `gorm:"column:x_axis"`
    Icon  string `gorm:"column:icon"`
    Yaxis string `gorm:"column:y_axis"`
    Data  int    `gorm:"column:data"`
}

// 2. 每個 component 一個 exported function，回傳對應的標準輸出型別
func GetXxxCount() ([]TwoDimensionalDataOutput, error) {
    var rows []XxxRow
    err := DBDashboard.Raw(`SELECT ...`).Scan(&rows).Error
    if err != nil {
        return nil, err
    }
    // 轉換為 TwoDimensionalDataOutput
    return []TwoDimensionalDataOutput{{Data: ...}}, nil
}
```

**重要**：
- 查 dashboard 資料用 `DBDashboard`；查 component 設定（components、query_charts 表）才用 `DBManager`
- SQL 寫在 model 函式的 Raw query 裡，不要放在 controller
- `three_d` / `percent` 的 grouping 邏輯（把 flat rows 變 `[]ThreeDimensionalDataOutput`）在 model 裡做好，controller 只負責 HTTP 層

### 3b. 新增 controller 檔 `app/controllers/<domain>.go`

```go
package controllers

func GetXxxCount(c *gin.Context) {
    data, err := models.GetXxxCount()
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
        return
    }
    c.JSON(http.StatusOK, gin.H{"status": "success", "data": data})
}
```

- `three_d` / `percent`：`c.JSON(http.StatusOK, gin.H{"status": "success", "data": data, "categories": categories})`
- `map_legend`：只回 `data`，無 `categories`

### 3c. 在 `app/routes/router.go` 新增路由

在 `ConfigureRoutes()` 加一行 `configureXxxRoutes()`，並在檔案末尾加：

```go
func configureXxxRoutes() {
    routes := RouterGroup.Group("/xxx/yyy")
    routes.Use(middleware.LimitAPIRequests(global.ComponentLimitAPIRequestsTimes, global.LimitRequestsDuration))
    routes.Use(middleware.LimitTotalRequests(global.ComponentLimitTotalRequestsTimes, global.LimitRequestsDuration))
    {
        routes.GET("/endpoint-a", controllers.GetXxxA)
        routes.GET("/endpoint-b", controllers.GetXxxB)
    }
}
```

### 3d. Build 確認

```bash
cd <BE_ROOT> && go build ./app/... 2>&1
```

Build 不過就先修，不要跳過。

---

## Step 4：Unit Test + 執行

### 4a. 寫 `app/models/<domain>_test.go`

測試連線設定放在 `initTestDB`：

```go
func initTestDB(t *testing.T) {
    t.Helper()
    if DBDashboard != nil {
        return
    }
    cfg := global.DatabaseConfig{
        Host:     getTestEnv("DB_DASHBOARD_HOST", "127.0.0.1"),
        Port:     getTestEnv("DB_DASHBOARD_PORT", "5432"),
        User:     getTestEnv("DB_DASHBOARD_USER", os.Getenv("USER")),
        Password: getTestEnv("DB_DASHBOARD_PASSWORD", ""),
        DBName:   getTestEnv("DB_DASHBOARD_DBNAME", "dashboard"),
        SSLMode:  getTestEnv("DB_DASHBOARD_SSLMODE", "disable"),
    }
    dsn := fmt.Sprintf("host=%s port=%s user=%s dbname=%s password=%s sslmode=%s",
        cfg.Host, cfg.Port, cfg.User, cfg.DBName, cfg.Password, cfg.SSLMode)
    db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
    if err != nil {
        t.Skipf("skip: cannot connect to test dashboard DB (%v)", err)
    }
    DBDashboard = db
}

func getTestEnv(key, fallback string) string {
    if v, ok := os.LookupEnv(key); ok { return v }
    return fallback
}
```

每個 component 對應一個 `TestGetXxx_<描述>` 函式，assert：
1. 函式不回 error
2. 輸出的長度/結構正確（例如 `len(data) == 1`、`len(categories) > 0`）
3. 數值與 Step 2 塞的假資料吻合（例如 active 筆數 = 5）

**用 `t.Skipf` 而非 `t.Fatalf` 處理連線失敗**，讓 CI 在沒有 DB 的環境不爆紅。

### 4b. 執行測試

```bash
cd <BE_ROOT> && go test ./app/models/ -run Test<Domain> -v -count=1
```

全部 `PASS` 才算完成。若有 pre-existing build error（例如 `non-constant format string`），順手修掉再跑。

### 4c. 回報

列出每個 test 名稱與 PASS/FAIL，以及執行輸出的最後幾行。

---

## Step 5（選填）：產出 OpenAPI YAML

若使用者要跟 FE 溝通，產出 `docs/<domain>_openapi.yaml`，格式 OpenAPI 3.0.3，包含：
- 每個 endpoint 的 summary + description（中文）
- 每個 response schema 的每個欄位都有 `description`（說明語意、允許值、型別注意事項）
- 真實的 `example`（對齊假資料的值）
- `$ref` 共用 schema 避免重複

YAML 要能貼進 Swagger Editor / Redoc 直接渲染，不要讓 FE 猜欄位意思。

---

## 快速參考：Taipei-City-Dashboard-BE 檔案位置

| 目的 | 路徑 |
|---|---|
| DB 連線全域變數 | `app/models/database.go`（`DBDashboard`、`DBManager`） |
| 標準 chart 型別 | `app/models/componentData.go` |
| BE Proxy 範例 | `app/controllers/isso.go` |
| Router 入口 | `app/routes/router.go` |
| 全域設定（port、env var）| `global/global.go` |
| Docker dashboard DB | `docker exec postgres-data psql -U postgres -d dashboard` |
| 本地 PG 確認 | `psql -h 127.0.0.1 -p 5432 -l` |
