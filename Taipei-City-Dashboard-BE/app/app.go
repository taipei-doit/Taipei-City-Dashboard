// Package app initiates the Gin server and connects to the postgreSQL database
package app

import (
	"os"

	"TaipeiCityDashboardBE/app/cache"
	"TaipeiCityDashboardBE/app/database"
	"TaipeiCityDashboardBE/app/initial"
	"TaipeiCityDashboardBE/app/middleware"
	"TaipeiCityDashboardBE/app/routes"
	"TaipeiCityDashboardBE/logs"

	"github.com/fvbock/endless"
	"github.com/gin-gonic/gin"
)

// app.go is the main entry point for this application.
// initiates configures the postgreSQL, Redis, Gin router and starts the server.

// StartApplication initiates the main backend application, including the Gin router, postgreSQL, and Redis.
func StartApplication() {
	// 1. Connect to postgreSQL and Redis
	database.ConnectToDatabases("MANAGER", "DASHBOARD")
	cache.ConnectToRedis()

	// 2. Initiate default Gin router with logger and recovery middleware
	routes.Router = gin.Default()

	// 3. Add common middlewares that need to run on all routes
	routes.Router.Use(middleware.AddCommonHeaders)

	// 4. Configure routes and routing groups (./router.go)
	routes.ConfigureRoutes()

	// 5. Configure http server
	addr := os.Getenv("DOMAIN") + ":" + os.Getenv("PORT")

	err := endless.ListenAndServe(addr, routes.Router)
	if err != nil {
		logs.Warn(err)
	}
	logs.FInfo("Server on %v stopped", addr)

	// If the server stops, close the database connections
	database.CloseConnects("MANAGER", "DASHBOARD")
	cache.CloseConnect()
}

func MigrateManagerSchema() {
	database.ConnectToDatabases("MANAGER")
	database.MigrateManagerSchema()
	initial.InitDashboardManager()
	database.CloseConnects("MANAGER")
}

func InsertDashbaordSampleData() {
	database.ConnectToDatabases("DASHBOARD")
	initial.InitSampleCityData()
	database.CloseConnects("DASHBOARD")
}
