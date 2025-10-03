// Package global stores all global variables and constants.
/*
Developed By Taipei Urban Intelligence Center 2023-2024

// Lead Developer:  Igor Ho (Full Stack Engineer)
// Systems & Auth: Ann Shih (Systems Engineer)
// Data Pipelines:  Iima Yu (Data Scientist)
// Design and UX: Roy Lin (Prev. Consultant), Chu Chen (Researcher)
// Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern)
*/
package global

import (
	"time"
)

const (
	// VERSION - is used to identify software version
	VERSION = "v1"

	// Request api limit times and duration
	AuthLimitAPIRequestsTimes          = 30000
	AuthLimitTotalRequestsTimes        = 60000
	UserLimitAPIRequestsTimes          = 10000
	UserLimitTotalRequestsTimes        = 50000
	ComponentLimitAPIRequestsTimes     = 20000
	ComponentLimitTotalRequestsTimes   = 100000
	ContributorLimitAPIRequestsTimes   = 10000
	ContributorLimitTotalRequestsTimes = 50000
	DashboardLimitAPIRequestsTimes     = 20000
	DashboardLimitTotalRequestsTimes   = 100000
	IssueLimitAPIRequestsTimes         = 20000
	IssueLimitTotalRequestsTimes       = 20000
	LimitRequestsDuration              = 600000 * time.Second

	// JWT Issuer
	JwtIssuer = "Taipei citydashboard"
	// JWT Expires Duration
	TokenExpirationDuration = 8 * time.Hour
	NotBeforeDuration       = -5 * time.Second

	TaipeipassAPIVersion = "v1.0.9"

	SampleDataDir = "/opt/db-sample-data/"
)
