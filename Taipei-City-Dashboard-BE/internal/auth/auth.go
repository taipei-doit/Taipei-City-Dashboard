// Package auth stores the authentication functions for the application. This includes controllers, middlewares, and utility functions.
package auth

import (
	"bytes"
	"crypto/sha256"
	"encoding/base64"
	"errors"
	"fmt"
	"net/http"
	"regexp"
	"strings"
	"time"

	"TaipeiCityDashboardBE/global"
	"TaipeiCityDashboardBE/internal/db/postgres"
	"TaipeiCityDashboardBE/internal/db/postgres/models"
	"TaipeiCityDashboardBE/logs"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

const (
	emailRegex = "^\\w+((-\\w+)|(\\.\\w+))*\\@[A-Za-z0-9]+((\\.|-)[A-Za-z0-9]+)*\\.[A-Za-z]+$"
)

func Login(c *gin.Context) {
	var user models.EmailUser
	var roleList []int
	var groupList []int

	const authPrefix = "Basic "

	credentials, err := getAuthFromRequest(c, authPrefix)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
		return
	}

	email, password, err := decodedCredentials(credentials)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
		return
	}

	// check parameters
	emailRegexp, err := regexp.MatchString(emailRegex, email)
	if err != nil || !emailRegexp {
		c.JSON(http.StatusUnauthorized, gin.H{"error": fmt.Errorf("invalid email format: %v", err)})
		return
	}

	if password == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "password is required"})
		return
	}

	// search DB to validate user password
	passwordSHA := hashString(password)
	if err := postgres.DBManager.
		Preload("Roles").
		Preload("Groups").
		Where("LOWER(email) = LOWER(?)", email).
		Where("password = ?", passwordSHA).
		First(&user).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Incorrect username or password"})
			return
		} else {
			logs.FError("Login failed: unexpected database error: %v", err)
			c.JSON(http.StatusUnauthorized, gin.H{"error": "unexpected database error"})
			return
		}
	}

	// check user is active
	if !user.IsActive.Bool {
		c.JSON(http.StatusForbidden, gin.H{"error": "User not activated"})
		return
	}

	// combine Roles into an array
	for _, group := range user.Roles {
		roleList = append(roleList, group.Id)
	}

	// combine Groups into an array
	for _, group := range user.Groups {
		groupList = append(groupList, group.Id)
	}

	// generate JWT token
	user.LoginAt = time.Now()
	token, err := GenerateJWT(user.LoginAt.Add(global.TokenExpirationDuration), "Email", user.Id, roleList, groupList)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": err.Error(),
		})
		return
	}

	// update last login time
	if err := postgres.DBManager.Save(&user).Error; err != nil {
		logs.FError("Failed to update login time: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "unexpected database error"})
		return
	}

	// return JWT token
	c.JSON(http.StatusOK, gin.H{
		"user":  user,
		"token": token,
	})
}

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

// GetUserInfoFromContext retrieves the user info from the Gin context.
func GetUserInfoFromContext(c *gin.Context) (string, int, time.Time, []int, []int) {
	// roles := c.GetStringSlice("roles")
	// accountStr := c.GetString("account")
	var (
		accountType string
		accountID   int
		roles       []int
		groups      []int
		expiresAt   time.Time
	)
	// get context keys
	accountType = c.GetString("accountType")
	accountID = c.GetInt("accountID")
	cRoles, existR := c.Get("roles")
	cGroups, existG := c.Get("groups")
	cExpiresAt := c.GetInt64("expiresAt")
	if !existR || !existG || cExpiresAt == 0 || accountType == "" || accountID == 0 {
		return "", 0, time.Time{}, nil, nil
	}
	// change type
	roles, _ = cRoles.([]int)
	groups, _ = cGroups.([]int)
	expiresAt = time.Unix(cExpiresAt, 0)

	return accountType, accountID, expiresAt, roles, groups
}

// hashPassword takes a password as input, hashes it using SHA-256, and returns the hexadecimal representation of the hash.
func hashString(s string) string {
	h := sha256.New()
	h.Write([]byte(s))
	return fmt.Sprintf("%x", h.Sum(nil))
}
