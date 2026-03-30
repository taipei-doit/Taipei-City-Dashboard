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
	"crypto/rand"
	"crypto/sha256"
	"errors"
	"fmt"
	"math/big"
	"time"

	"github.com/gin-gonic/gin"
)

// GenerateRandomString generates a random alphanumeric string of a specified length.
func GenerateRandomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	result := make([]byte, length)
	for i := range result {
		num, err := rand.Int(rand.Reader, big.NewInt(int64(len(charset))))
		if err != nil {
			return ""
		}
		result[i] = charset[num.Int64()]
	}
	return string(result)
}

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
func GetTime(c *gin.Context) (string, string, error) {
	timefrom := c.Query("timefrom")
	timeto := c.Query("timeto")

	layout := "2006-01-02T15:04:05+08:00" // 定義時間格式

	// timeFrom defaults to 1990-01-01 (essentially, all data)
	if timefrom == "" {
		timefrom = time.Date(1990, 1, 1, 0, 0, 0, 0, time.FixedZone("UTC+8", 8*60*60)).Format(layout)
	} else {
		// 檢查 timefrom 格式
		if _, err := time.Parse(layout, timefrom); err != nil {
			return "", "", errors.New("timefrom 格式無效")
		}
	}
	// timeTo defaults to current time
	if timeto == "" {
		timeto = time.Now().Format(layout)
	} else {
		// 檢查 timeto 格式
		if _, err := time.Parse(layout, timeto); err != nil {
			return "", "", errors.New("timeto 格式無效")
		}
	}

	return timefrom, timeto, nil
}