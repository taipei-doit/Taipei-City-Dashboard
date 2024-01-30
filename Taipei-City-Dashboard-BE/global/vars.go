package global

import (
	"os"

	"TaipeiCityDashboardBE/logs"
)

var (
	JwtSecret              string
	IssoURL                string
	IssoClientID           string
	IssoClientSecret       string
	TaipeipassURL          string
	TaipeipassClientID     string
	TaipeipassClientSecret string
)

func init() {
	// get os enviroments
	env := os.Getenv("ENV")
	JwtSecret = os.Getenv("JwtSecret")
	IssoClientID = os.Getenv("IssoClientID")
	IssoClientSecret = os.Getenv("IssoClientSecret")
	// TaipeipassClientID = os.Getenv("TaipeipassClientID")
	// TaipeipassClientSecret = os.Getenv("TaipeipassClientSecret")

	// 判斷環境變數的值
	switch env {
	case "prod":
		// 設定 production 相關的變數
		IssoURL = IssoURLProd
		TaipeipassURL = TaipeipassURLProd
		logs.FInfo("Using production environment.")
	case "develop":
		// 設定 develop 相關的變數
		IssoURL = IssoURLDev
		TaipeipassURL = TaipeipassURLDev
		logs.FInfo("Using development environment.")
	default:
		// 預設值或錯誤處理
		IssoURL = IssoURLDev
		TaipeipassURL = TaipeipassURLDev
		logs.FInfo("Unknown environment. Defaulting to development environment.")
	}
}
