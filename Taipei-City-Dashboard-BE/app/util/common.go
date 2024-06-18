// Package util stores the utility functions for the application (functions that only handle internal logic)
/*
Developed By Taipei Urban Intelligence Center 2023-2024

// Lead Developer:  Igor Ho (Full Stack Engineer)
// Systems & Auth: Ann Shih (Systems Engineer)
// Data Pipelines:  Iima Yu (Data Scientist)
// Design and UX: Roy Lin (Prev. Consultant), Chu Chen (Researcher)
// Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern)
*/
package util

import (
	"crypto/sha256"
	"fmt"
	"time"

	"github.com/gin-gonic/gin"
)

// HashString takes a string as input, hashes it using SHA-256, and returns the hexadecimal representation of the hash.
func HashString(s string) string {
	h := sha256.New()
	h.Write([]byte(s))
	return fmt.Sprintf("%x", h.Sum(nil))
}

// MergeAndRemoveDuplicates merges multiple integer slices and removes duplicates.
func MergeAndRemoveDuplicates(slices ...[]int) []int {
	merged := make(map[int]struct{})

	// Merge two slices and remove duplicates
	for _, slice := range slices {
		for _, item := range slice {
			merged[item] = struct{}{}
		}
	}

	// Convert to slice
	result := make([]int, 0, len(merged))
	for item := range merged {
		result = append(result, item)
	}

	return result
}

// GetTime is a utility function to get the time from the header and set default values.
func GetTime(c *gin.Context) (string, string) {
	timefrom := c.Query("timefrom")
	timeto := c.Query("timeto")

	// timeFrom defaults to 1990-01-01 (essentially, all data)
	if timefrom == "" {
		timefrom = time.Date(1990, 1, 1, 0, 0, 0, 0, time.FixedZone("UTC+8", 8*60*60)).Format("2006-01-02T15:04:05+08:00")
	}
	// timeTo defaults to current time
	if timeto == "" {
		timeto = time.Now().Format("2006-01-02T15:04:05+08:00")
	}

	return timefrom, timeto
}
