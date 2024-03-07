// Package util stores the utility functions for the application (functions that only handle internal logic)
package util

import (
	"bytes"
	"encoding/base64"
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"

	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/global"

	"github.com/dgrijalva/jwt-go"
	"github.com/gin-gonic/gin"
)

// GetAuthFromRequest retrieves authentication information from the HTTP request headers and returns the decoded email and password from the Authorization header.
func GetAuthFromRequest(c *gin.Context, basicPrefix string) (string, error) {
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

func DecodeCredentials(credentials string) (email, password string, err error) {
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

var jwtSecret = []byte(global.JwtSecret)

// GenerateJWT generates a JWT token using the provided information.
// It includes user type, user ID, role list, group list, and expiration details in the JWT claims.
// The token is signed using HS256 and returned as a string.
func GenerateJWT(ExpiresAt time.Time, loginType string, userID int, isAdmin bool, permissions []models.Permission) (string, error) {
	// Create a unique user ID for JWT
	now := time.Now()
	uid := loginType + strconv.FormatInt(int64(userID), 10)
	jwtID := uid + strconv.FormatInt(now.Unix(), 10)

	// Set JWT claims and sign
	claims := models.Claims{
		LoginType:   loginType,
		AccountID:   userID,
		IsAdmin:     isAdmin,
		Permissions: permissions,
		StandardClaims: jwt.StandardClaims{
			Audience:  uid,
			ExpiresAt: ExpiresAt.Unix(),
			Id:        jwtID,
			IssuedAt:  now.Unix(),
			Issuer:    "Taipei citydashboard",
			NotBefore: now.Add(global.NotBeforeDuration).Unix(),
			Subject:   uid,
		},
	}

	// Sign the claims using JWT signing method HS256 and obtain the token string
	tokenClaims := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	token, err := tokenClaims.SignedString(jwtSecret)
	if err != nil {
		return "", fmt.Errorf("generate JWT token error: %v", err)
	}

	return token, nil
}

// HasPermission checks if the permissions contain a specific groupid and roleid.
func HasPermission(permissions []models.Permission, targetGroupID, targetRoleID int) bool {
	for _, perm := range permissions {
		if perm.GroupID == targetGroupID && perm.RoleID == targetRoleID {
			return true
		}
	}
	return false
}

// GetPermissionAllGroupIDs extracts unique group IDs from a list of permissions.
func GetPermissionAllGroupIDs(permissions []models.Permission) []int {
	uniqueGroupIDs := make(map[int]struct{})

	// Extract unique group IDs from permissions
	for _, perm := range permissions {
		uniqueGroupIDs[perm.GroupID] = struct{}{}
	}

	// Convert unique group IDs to a slice
	groupIDs := make([]int, 0, len(uniqueGroupIDs))
	for groupID := range uniqueGroupIDs {
		groupIDs = append(groupIDs, groupID)
	}

	return groupIDs
}

// GetPermissionGroupIDs extracts unique group IDs from permissions based on a specific role.
func GetPermissionGroupIDs(permissions []models.Permission, role int) []int {
	uniqueGroupIDs := make(map[int]struct{})

	// Extract unique group IDs from permissions for the specified role
	for _, perm := range permissions {
		if perm.RoleID == role {
			uniqueGroupIDs[perm.GroupID] = struct{}{}
		}
	}

	// Convert unique group IDs to a slice
	groupIDs := make([]int, 0, len(uniqueGroupIDs))
	for groupID := range uniqueGroupIDs {
		groupIDs = append(groupIDs, groupID)
	}

	return groupIDs
}
