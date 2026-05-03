> **w01**
> 本文僅涵蓋後端的程式碼撰寫規範。如果您也將開發我們的前端，請參閱[前端程式碼撰寫規範](/front-end/code-style)。

## 程式碼檢查

本專案使用 `gopls` 來格式化和檢查程式碼。當您安裝 VSCode 的 Go 擴充套件時，此工具會自動包含在內。在根目錄下，有一個名為 `.vscode` 的資料夾，其中包含 VSCode 的設定，這將使您在儲存文件時，能夠按照我們的指南格式化您的程式碼。請不要擅自修改以上設定。在開啟 pull request 之前，您必須確保 gopls 顯示的所有警告和錯誤都已解決。開啟 pull request 的流程將在[此處](/back-end/open-a-pull-request)詳細說明。

## 變數和檔案命名

一般而言，所有新的變數和檔案名稱都應該是獨特且描述性的。如果您的貢獻包含不清楚的變數或檔案名稱，您將被要求修改它們。以下列出了一些更具體的指南。

### 資料夾

由於 Go 將資料夾視為套件，因此所有新的資料夾名稱都應該是獨特且簡潔的，最好是小寫的單字（例如 `db`）。

### 檔案

所有新的檔案名稱都應該是簡潔的，最好是小寫的單字。如果檔案包含多個單字，則應該使用 Camel case（例如 `componentConfig.go`）。

### 變數和函式

根據 Go 的規範，應該使用 Pascal case（例如 `GetAllComponents`，首字母大寫）來命名全域的變數和函式，而只在套件內使用的變數和函式應該使用 Camel case（例如 `createTempComponentDB`）。此外，我們強烈建議函式名稱以動詞開頭，例如 set、handle、execute、show 等等。

## 文件結構

一般而言，所有文件都應該按照清晰和邏輯的順序進行格式化。必要時應添加註解以增加清晰度。如果您的貢獻包含未按照本專案標準格式化的文件，您將被要求修改它們。以下列出了一些更具體的指南。

```go
// Package postgres... (1. 套件宣告 + 套件描述)
package postgres

// (2. 匯入)
import (
	// (2.1 標準庫的匯入)
	"crypto/sha256"
	"fmt"
	"os"
	"time"

	// (2.2 內部匯入)
	"TaipeiCityDashboardBE/internal/db/postgres/models"
	"TaipeiCityDashboardBE/logs"

	// (2.3 第三方匯入)
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// (3. 全域變數或結構，如果適用的話)
var (
	DBDashboard *gorm.DB
	DBManager   *gorm.DB
)

// (4. 函式)
func ConnectToDatabases(dbNames ...interface{}) {
	// ...
}
```