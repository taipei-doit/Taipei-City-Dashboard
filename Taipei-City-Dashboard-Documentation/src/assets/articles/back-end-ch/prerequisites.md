## 開發環境

為了最佳的開發體驗，我們建議使用作業系統為 Windows 或 macOS 的電腦。我們也建議進行以下開發環境設定。

### 開發工具

如果您希望使用我們的[專案設定指南](/back-end/project-setup)，請確保您的電腦上有安裝了以下開發工具：[Go](https://golang.org/)、[Git](https://git-scm.com/)（也可以額外安裝 GitHub Desktop）、Docker (建議透過安裝 [Docker Desktop](https://www.docker.com/products/docker-desktop/))、[Postman](https://www.postman.com/)。如果您也會開發我們的前端，亦請安裝 [Node.js LTS](https://nodejs.org/en).

### 程式編輯器

[VScode](https://code.visualstudio.com/) 是我們首選的程式編輯器。我們建議安裝以下擴充工具：Go、Docker。如果您也會開發我們的前端，我們亦建議安裝 Prettier、ESLint、Vue Language Features (Volar) 等擴充工具。如果您選擇其他程式編輯器，請確保它支持上述擴充工具。

## 技術堆疊

### Go

Go 是本專案的主要程式語言。Go 的文件和安裝指南可以在[這裡](https://golang.org/doc/)找到。

### PostgreSQL

本專案使用 PostgreSQL 作為資料庫。PostgreSQL 的文件可以在[這裡](https://www.postgresql.org/docs/)找到。

### Redis

本專案使用 Redis 作為快取工具，用來儲存常被請求的資訊。Redis 的文件可以在[這裡](https://redis.io/docs/)找到。

## Go 核心函式庫和套件

### Cobra

Cobra 是一個用來在 Go 中建立 CLI 應用程式的函式庫。本專案使用 Cobra 來執行必要的任務，而不會干擾主要的後端服務。Cobra 的文件可以在[這裡](https://cobra.dev/)找到。

### Gin

Gin 是一個用來在 Go 中建立網路應用程式的框架。Gin 的文件可以在[這裡](https://gin-gonic.com/docs/)找到。

### GORM

GORM 是一個用來在 Go 中連接資料庫（例如 PostgreSQL）的 ORM 函式庫。GORM 的文件可以在[這裡](https://gorm.io/docs/)找到。

### Redis

Redis 是一個用來連接 Redis 的函式庫。Redis 的文件可以在[這裡](https://pkg.go.dev/github.com/go-redis/redis/v8)找到。
