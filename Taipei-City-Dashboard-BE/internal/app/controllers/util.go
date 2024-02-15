package controllers

import (
	"time"

	"github.com/gin-gonic/gin"
)

// utilGetTime is a utility function to get the time from the header and set default values.
func utilGetTime(c *gin.Context) (string, string) {
	timeFrom := c.GetHeader("Time_from")
	timeTo := c.GetHeader("Time_to")

	// timeFrom defaults to 1990-01-01 (essentially, all data)
	if timeFrom == "" {
		timeFrom = time.Date(1990, 1, 1, 0, 0, 0, 0, time.FixedZone("UTC+8", 8*60*60)).Format("2006-01-02T15:04:05+08:00")
	}
	// timeTo defaults to current time
	if timeTo == "" {
		timeTo = time.Now().Format("2006-01-02T15:04:05+08:00")
	}

	return timeFrom, timeTo
}
