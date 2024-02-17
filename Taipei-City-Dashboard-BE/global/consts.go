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
	ComponentLimitAPIRequestsTimes   = 200
	ComponentLimitTotalRequestsTimes = 1000
	DashboardLimitAPIRequestsTimes   = 80
	DashboardLimitTotalRequestsTimes = 400
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
