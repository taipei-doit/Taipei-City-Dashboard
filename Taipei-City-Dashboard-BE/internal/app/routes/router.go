// Package routes stores all the routes for the Gin router.
package routes

import (
	"TaipeiCityDashboardBE/global"
	"TaipeiCityDashboardBE/internal/app/controllers"
	"TaipeiCityDashboardBE/internal/app/middleware"
	"TaipeiCityDashboardBE/internal/auth"

	"github.com/gin-gonic/gin"
)

// router.go configures all API routes

var (
	Router      *gin.Engine
	RouterGroup *gin.RouterGroup
)

// ConfigureRoutes configures all routes for the API and sets version router groups.
func ConfigureRoutes() {
	// taipeipass login callback
	Router.GET("/callback", auth.ExecIssoAuth) // will move to configureAuthRoutes function

	Router.Use(auth.ValidateJWT)
	// API routers
	RouterGroup = Router.Group("/api/" + global.VERSION)
	configureAuthRoutes()
	configureComponentRoutes()
	configureDashboardRoutes()
	configureIssueRoutes()
}

func configureAuthRoutes() {
	// auth routers
	authRoutes := RouterGroup.Group("/auth")
	authRoutes.Use(middleware.LimitAPIRequests(global.AuthLimitAPIRequestsTimes, global.LimitRequestsDuration))
	authRoutes.Use(middleware.LimitTotalRequests(global.AuthLimitTotalRequestsTimes, global.TokenExpirationDuration))
	authRoutes.POST("/login", auth.Login)
	// // taipeipass login callback
	// authRoutes.GET("/callback", auth.ExecIssoAuth)
}

// configureComponentRoutes configures all component routes.
func configureComponentRoutes() {
	componentRoutes := RouterGroup.Group("/component")

	componentRoutes.Use(middleware.LimitAPIRequests(global.ComponentLimitAPIRequestsTimes, global.LimitRequestsDuration))
	componentRoutes.Use(middleware.LimitTotalRequests(global.ComponentLimitTotalRequestsTimes, global.TokenExpirationDuration))
	{
		componentRoutes.GET("/", controllers.GetAllComponents)
		componentRoutes.
			GET("/:id", controllers.GetComponentByID)
		componentRoutes.
			GET("/:id/chart", controllers.GetComponentChartData)
		componentRoutes.GET("/:id/history", controllers.GetComponentHistoryData)
	}
	componentRoutes.Use(middleware.LimitRequestTo([]int{1}))
	{
		componentRoutes.
			PATCH("/:id", controllers.UpdateComponent).
			DELETE("/:id", controllers.DeleteComponent)
		componentRoutes.
			PATCH("/:id/chart", controllers.UpdateComponentChartConfig)
		componentRoutes.PATCH("/:id/map", controllers.UpdateComponentMapConfig)
	}
}

func configureDashboardRoutes() {
	dashboardRoutes := RouterGroup.Group("/dashboard")
	// dashboardRoutes.Use(auth.ValidateJWT)
	dashboardRoutes.Use(middleware.LimitAPIRequests(global.DashboardLimitAPIRequestsTimes, global.LimitRequestsDuration))
	dashboardRoutes.Use(middleware.LimitTotalRequests(global.DashboardLimitTotalRequestsTimes, global.LimitRequestsDuration))
	{
		dashboardRoutes.
			GET("/", controllers.GetAllDashboards)
		dashboardRoutes.
			GET("/:index", controllers.GetDashboardByIndex)
	}
	dashboardRoutes.Use(middleware.LimitRequestTo([]int{1, 2}))
	{
		dashboardRoutes.POST("/", controllers.CreatePersonalDashboard)
		dashboardRoutes.
			PATCH("/:index", controllers.UpdateDashboard).
			DELETE("/:index", controllers.DeleteDashboard)
	}
	dashboardRoutes.Use(middleware.LimitRequestTo([]int{1}))
	{
		dashboardRoutes.POST("/public", controllers.CreatePublicDashboard)
		dashboardRoutes.GET("/check-index/:index", controllers.CheckDashboardIndex)
	}
}

func configureIssueRoutes() {
	issueRoutes := RouterGroup.Group("/issue")
	// issueRoutes.Use(auth.ValidateJWT)
	issueRoutes.Use(middleware.LimitAPIRequests(global.IssueLimitAPIRequestsTimes, global.LimitRequestsDuration))
	issueRoutes.Use(middleware.LimitTotalRequests(global.IssueLimitTotalRequestsTimes, global.LimitRequestsDuration))
	{
		issueRoutes.
			POST("/", controllers.CreateIssue)
	}
	issueRoutes.Use(middleware.LimitRequestTo([]int{1}))
	{
		issueRoutes.
			GET("/", controllers.GetAllIssues)
		issueRoutes.
			PATCH("/:id", controllers.UpdateIssueByID)
	}
}
