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
	AuthLimitAPIRequestsTimes          = 300
	AuthLimitTotalRequestsTimes        = 600
	UserLimitAPIRequestsTimes          = 100
	UserLimitTotalRequestsTimes        = 500
	ComponentLimitAPIRequestsTimes     = 200
	ComponentLimitTotalRequestsTimes   = 1000
	ContributorLimitAPIRequestsTimes   = 100
	ContributorLimitTotalRequestsTimes = 500
	DashboardLimitAPIRequestsTimes     = 200
	DashboardLimitTotalRequestsTimes   = 1000
	IssueLimitAPIRequestsTimes         = 20
	IssueLimitTotalRequestsTimes       = 200
	LimitRequestsDuration              = 60 * time.Second

	// JWT Issuer
	JwtIssuer = "Taipei citydashboard"
	// JWT Expires Duration
	TokenExpirationDuration = 8 * time.Hour
	NotBeforeDuration       = -5 * time.Second

	TaipeipassAPIVersion = "v1.0.9"

	SampleDataDir = "/opt/db-sample-data/"
)
