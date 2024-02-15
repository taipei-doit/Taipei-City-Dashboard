// Package app initiates the Gin server and connects to the postgreSQL database
package app

import (
	"os"

	"TaipeiCityDashboardBE/internal/app/initial"
	"TaipeiCityDashboardBE/internal/app/middleware"
	"TaipeiCityDashboardBE/internal/app/routes"
	"TaipeiCityDashboardBE/internal/db/cache"
	"TaipeiCityDashboardBE/internal/db/postgres"
	"TaipeiCityDashboardBE/logs"

	"github.com/fvbock/endless"
	"github.com/gin-gonic/gin"
)

// app.go is the main entry point for this application.
// initiates configures the postgreSQL, Redis, Gin router and starts the server.

// StartApplication initiates the main backend application, including the Gin router, postgreSQL, and Redis.
func StartApplication() {
	// 1. Connect to postgreSQL and Redis
	postgres.ConnectToDatabases("MANAGER", "DASHBOARD")
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
	postgres.CloseConnects("MANAGER", "DASHBOARD")
	cache.CloseConnect()
}

func MigrateManagerSchema() {
	postgres.ConnectToDatabases("MANAGER")
	postgres.MigrateManagerSchema()
	initial.InitDashboardManager()
	postgres.CloseConnects("MANAGER")
}

func InsertDashbaordSampleData() {
	postgres.ConnectToDatabases("DATA")
	initial.InitSampleCityData()
	postgres.CloseConnects("DATA")
}
