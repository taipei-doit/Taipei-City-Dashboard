## 全域服務

### Cobra

Cobra 指令儲存在 `/cmd/root.go`。如果啟動應用程式時未指定執行指令，應用程式會執行 `TaipeiCityDashboardBE` 指令。本專案亦包含其他指令如 `migrateDB`等。

### Logs

Logs 的相關設定儲存在 `/logs/logs.go`，為應用程式提供全域 logging。

### 全域變量 (global variables)

全域變量儲存在 `/global/consts.go` 和 `/global/vars.go`。前者包含應用程式中使用的所有常量，而後者讀取並儲存專案的環境變量。

## App

主應用程式儲存在 `/app/app.go`。它包含一個 `StartApplication` 函式，用來初始化應用程式並啟動伺服器。在 `/app` 中，還有六個額外的資料夾，包含應用程式的 router 、 middleware 、 controller 、 資料庫 handler、暫存 handler 和 utility 函式。

### Router

Router 儲存在 `/app/router/router.go`。它包含應用程式的所有路徑。在[下下章](/back-end/authentication-apis)將提供有關此應用程式中可用路徑的更多資訊。

### Middlewares

Middleware 儲存在 `/app/middlewares`。這些 middleware 控制 API 呼叫頻率、身份驗證、權限管理等。

### Controllers

Controller 儲存在 `/app/controllers`。這些 controller 處理身份驗證和應用程式的運行邏輯。在[下一章之後](/back-end/authentication-apis)將提供有關此應用程式中可用 controller 的更多資訊。

### 資料庫 (Database)

連接到 PostgreSQL 資料庫的主要邏輯儲存在 `/app/models/database.go`。資料庫的連線透過 `DBDashboard`（與 `dashboard` 資料庫的連線）和 `DBManager`（與 `dashboardmanager` 資料庫的連線）變量在應用程式全域中均可使用。

資料庫的 model 和 handler 儲存在 `/app/models`，檔名與使用它們的 controller 檔名相同。例如，`/models/dashboard.go` 檔案包含由 `/controllers/dashboard.go` 中的 controller 使用的 `Dashboard` 模型。

### 暫存 (Cache)

連接到 Redis cache 的主要邏輯儲存在 `/app/cache/redis.go`。連線透過 `Redis` 變量在應用程式全域中均可使用。

### Utilities

Utility 函式儲存在 `/app/utils`。這些函式在 middleware 、 controller 和資料庫 handler 中使用。

> **i01**
> 當建立新函式時，請將其歸類在 `/app` 中相對應的資料夾中。
>
> 處理 request 並將其傳遞給 controller 的函式，請將其放在 `/app/middlewares` 資料夾中；處理 request 並回應給客戶端的函式，請將其放在 `/app/controllers` 資料夾中；與資料庫溝通的函式，請將其放在 `/app/models` 資料夾中；不屬於上述類別的函式，請將其放在 `/app/utils` 資料夾中。
