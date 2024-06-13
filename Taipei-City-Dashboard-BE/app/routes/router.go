// Package routes stores all the routes for the Gin router.
/*
Developed By Taipei Urban Intelligence Center 2023-2024

// Lead Developer:  Igor Ho (Full Stack Engineer)
// Systems & Auth: Ann Shih (Systems Engineer)
// Data Pipelines:  Iima Yu (Data Scientist)
// Design and UX: Roy Lin (Prev. Consultant), Chu Chen (Researcher)
// Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern)
*/
package routes

import (
	"TaipeiCityDashboardBE/app/controllers"
	"TaipeiCityDashboardBE/app/middleware"
	"TaipeiCityDashboardBE/global"

	"github.com/gin-gonic/gin"
)

// router.go configures all API routes

var (
	Router      *gin.Engine
	RouterGroup *gin.RouterGroup
)

// ConfigureRoutes configures all routes for the API and sets version router groups.
func ConfigureRoutes() {
	Router.Use(middleware.ValidateJWT)
	// API routers
	RouterGroup = Router.Group("/api/" + global.VERSION)
	configureAuthRoutes()
	configureUserRoutes()
	configureComponentRoutes()
	configureDashboardRoutes()
	configureIssueRoutes()
	configureIncidentRoutes()
	// configureWsRoutes()
	configureContributorRoutes()
}

func configureAuthRoutes() {
	// auth routers
	authRoutes := RouterGroup.Group("/auth")
	authRoutes.Use(middleware.LimitAPIRequests(global.AuthLimitAPIRequestsTimes, global.LimitRequestsDuration))
	authRoutes.Use(middleware.LimitTotalRequests(global.AuthLimitTotalRequestsTimes, global.TokenExpirationDuration))
	authRoutes.POST("/login", controllers.Login)
	// taipeipass login callback
	authRoutes.GET("/callback", controllers.ExecIssoAuth)
	authRoutes.POST("/logout", controllers.IssoLogOut)
}

func configureUserRoutes() {
	userRoutes := RouterGroup.Group("/user")
	userRoutes.Use(middleware.LimitAPIRequests(global.UserLimitAPIRequestsTimes, global.LimitRequestsDuration))
	userRoutes.Use(middleware.LimitTotalRequests(global.UserLimitTotalRequestsTimes, global.TokenExpirationDuration))
	userRoutes.Use(middleware.IsLoggedIn())
	{
		userRoutes.GET("/me", controllers.GetUserInfo)
		userRoutes.PATCH("/me", controllers.EditUserInfo)
		userRoutes.POST("/:id/viewpoint", controllers.CreateViewPoint)
		userRoutes.GET("/:id/viewpoint", controllers.GetViewPointByUserID)
		userRoutes.DELETE("/:id/viewpoint/:viewpointid", controllers.DeleteViewPoint)
	}
	userRoutes.Use(middleware.IsSysAdm())
	{
		userRoutes.GET("/", controllers.GetAllUsers)
		userRoutes.PATCH("/:id", controllers.UpdateUserByID)
	}
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
	componentRoutes.Use(middleware.IsSysAdm())
	{
		componentRoutes.
			POST("/", controllers.CreateComponent).
			PATCH("/:id", controllers.UpdateComponent).
			DELETE("/:id", controllers.DeleteComponent)
		componentRoutes.
			PATCH("/:id/chart", controllers.UpdateComponentChartConfig)
		componentRoutes.PATCH("/:id/map", controllers.UpdateComponentMapConfig)
	}
}

func configureDashboardRoutes() {
	dashboardRoutes := RouterGroup.Group("/dashboard")
	dashboardRoutes.Use(middleware.LimitAPIRequests(global.DashboardLimitAPIRequestsTimes, global.LimitRequestsDuration))
	dashboardRoutes.Use(middleware.LimitTotalRequests(global.DashboardLimitTotalRequestsTimes, global.LimitRequestsDuration))
	{
		dashboardRoutes.
			GET("/", controllers.GetAllDashboards)
		dashboardRoutes.
			GET("/:index", controllers.GetDashboardByIndex)
	}
	dashboardRoutes.Use(middleware.IsLoggedIn())
	{
		dashboardRoutes.POST("/", controllers.CreatePersonalDashboard)
		dashboardRoutes.
			PATCH("/:index", controllers.UpdateDashboard).
			DELETE("/:index", controllers.DeleteDashboard)
	}
	dashboardRoutes.Use(middleware.IsSysAdm())
	{
		dashboardRoutes.POST("/public", controllers.CreatePublicDashboard)
		dashboardRoutes.GET("/check-index/:index", controllers.CheckDashboardIndex)
	}
}

func configureIssueRoutes() {
	issueRoutes := RouterGroup.Group("/issue")
	issueRoutes.Use(middleware.LimitAPIRequests(global.IssueLimitAPIRequestsTimes, global.LimitRequestsDuration))
	issueRoutes.Use(middleware.LimitTotalRequests(global.IssueLimitTotalRequestsTimes, global.LimitRequestsDuration))
	issueRoutes.Use(middleware.IsLoggedIn())
	{
		issueRoutes.
			POST("/", controllers.CreateIssue)
	}
	issueRoutes.Use(middleware.IsSysAdm())
	{
		issueRoutes.
			GET("/", controllers.GetAllIssues)
		issueRoutes.
			PATCH("/:id", controllers.UpdateIssueByID)
	}
}

func configureIncidentRoutes() {
	incidentRoutes := RouterGroup.Group("/incident")
	incidentRoutes.Use(middleware.LimitAPIRequests(global.IssueLimitAPIRequestsTimes, global.LimitRequestsDuration))
	incidentRoutes.Use(middleware.LimitTotalRequests(global.IssueLimitTotalRequestsTimes, global.LimitRequestsDuration))
	incidentRoutes.Use(middleware.IsLoggedIn())
	incidentRoutes.Use(middleware.IsSysAdm())
	{
		incidentRoutes.GET("/", controllers.GetIncident)
		incidentRoutes.POST("/", controllers.CreateIncident)
		incidentRoutes.PATCH("/:id", controllers.UpdateIncidentByID)
		incidentRoutes.DELETE("/", controllers.DeleteIncident)
	}
}

func configureContributorRoutes() {
	contributorRoutes := RouterGroup.Group("/contributor")
	contributorRoutes.Use(middleware.LimitAPIRequests(global.ContributorLimitAPIRequestsTimes, global.LimitRequestsDuration))
	contributorRoutes.Use(middleware.LimitTotalRequests(global.ContributorLimitTotalRequestsTimes, global.TokenExpirationDuration))
	{
		contributorRoutes.GET("/", controllers.GetAllContributors)
	}
	contributorRoutes.Use(middleware.IsSysAdm())
	{
		contributorRoutes.POST("/", controllers.CreateContributor)
		contributorRoutes.PATCH("/:id", controllers.UpdateContributor)
		contributorRoutes.DELETE("/:id", controllers.DeleteContributor)
	}
}

// func configureWsRoutes() {
// 	wsRoutes := RouterGroup.Group("/ws")
// 	wsRoutes.Use(middleware.LimitAPIRequests(global.IssueLimitAPIRequestsTimes, global.LimitRequestsDuration))
// 	wsRoutes.Use(middleware.LimitTotalRequests(global.IssueLimitTotalRequestsTimes, global.LimitRequestsDuration))
// 	wsRoutes.Use(middleware.IsLoggedIn())
// 	wsRoutes.Use(middleware.IsSysAdm())
// 	{
// 		wsRoutes.GET("/", controllers.ServeWs)
// 		wsRoutes.PUT("/write/", controllers.WriteMap)
// 	}
// }
