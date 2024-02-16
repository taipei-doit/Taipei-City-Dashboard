package auth

import (
	"bytes"
	"crypto/sha256"
	"encoding/base64"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

// getAuthFromRequest retrieves authentication information from the HTTP request headers.
// It returns the decoded email and password from the Authorization header.
func getAuthFromRequest(c *gin.Context, basicPrefix string) (string, error) {
	// const basicPrefix = "Basic "
	// Get the Authorization header from the request
	auth := c.GetHeader("Authorization")

	// Check if Authorization is empty
	if auth == "" {
		return "", errors.New("authorization header is missing")
	}

	// Check if Authorization starts with "Basic "
	if !strings.HasPrefix(auth, basicPrefix) {
		return "", errors.New("invalid authorization header")
	}

	// Decode user's email and password
	credentials := strings.Split(auth, basicPrefix)[1]
	return credentials, nil
}

// GetUserInfoFromContext retrieves the user info from the Gin context.
func GetUserInfoFromContext(c *gin.Context) (loginType string, accountID int, isAdmin bool, expiresAt time.Time, permissions []Permission) {
	// get context keys
	loginType = c.GetString("loginType")
	accountID = c.GetInt("accountID")
	isAdmin = c.GetBool("isAdmin")
	expiresAt = c.GetTime("expiresAt")
	// Retrieve permissions from the context
	if perms, exists := c.Get("permissions"); exists {
		// Check if the value exists
		if permsList, ok := perms.([]Permission); ok {
			permissions = permsList
		}
	}
	return
}

func decodedCredentials(credentials string) (email, password string, err error) {
	decodedCredentials, err := base64.StdEncoding.DecodeString(credentials)
	if err != nil {
		return "", "", fmt.Errorf("decode auth credentials error: %v", err)
	}

	splitCredentials := bytes.Split(decodedCredentials, []byte(":"))
	if len(splitCredentials) < 2 {
		return "", "", errors.New("credentials are incorrect")
	}

	email = string(splitCredentials[0])
	password = string(splitCredentials[1])
	return email, password, nil
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
