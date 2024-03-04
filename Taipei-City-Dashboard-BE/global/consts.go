// Package global stores all global variables and constants.
package global

import (
	"time"
)

const (
	// VERSION - is used to identify software version
	VERSION = "v1"

	// Request api limit times and duration
	AuthLimitAPIRequestsTimes        = 300
	AuthLimitTotalRequestsTimes      = 600
	UserLimitAPIRequestsTimes        = 100
	UserLimitTotalRequestsTimes      = 500
	ComponentLimitAPIRequestsTimes   = 200
	ComponentLimitTotalRequestsTimes = 1000
	DashboardLimitAPIRequestsTimes   = 200
	DashboardLimitTotalRequestsTimes = 1000
	IssueLimitAPIRequestsTimes       = 20
	IssueLimitTotalRequestsTimes     = 200
	LimitRequestsDuration            = 60 * time.Second

	// JWT secret
	// JWT Issuer
	JwtIssuer = "Taipei citydashboard"
	// JWT Expires Duration
	TokenExpirationDuration = 8 * time.Hour
	NotBeforeDuration       = 0 * time.Second

	// TaipeipassURLProd ...
	TaipeipassURLProd = "https://id.taipei/tpcd"
	// TaipeipassURLDev ...
	TaipeipassURLDev = "https://demo.jrsys.com.tw/tpcd"
	// IssoURLProd ...
	IssoURLProd = "https://id.taipei/isso"
	// IssoURLDev ...
	IssoURLDev = "https://demo.jrsys.com.tw/isso"

	TaipeipassAPIVersion = "v1.0.9"
)
