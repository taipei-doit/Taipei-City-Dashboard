package middleware

import (
	"net/http"

	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/util"
	"TaipeiCityDashboardBE/global"

	"github.com/dgrijalva/jwt-go"
	"github.com/gin-gonic/gin"
)

var jwtSecret = []byte(global.JwtSecret)

func ValidateJWT(c *gin.Context) {
	const authPrefix = "Bearer "
	token, err := util.GetAuthFromRequest(c, authPrefix)
	// logs.FError(err.Error())
	if err != nil {
		// c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
		// c.Abort()
		// If there is an error in extracting the token from the request,
		// set group:public role:viewer permission and proceed to the next middleware.
		c.Set("loginType", "no login")
		c.Set("accountID", 0)
		c.Set("isAdmin", false)
		permissions := []models.Permission{
			{GroupID: 1, RoleID: 3},
		}
		c.Set("permissions", permissions)
		c.Next()
		return
	}

	/*
		Parse and validate token for six things:
			validationErrorMalformed => token is malformed
			validationErrorUnverifiable => token could not be verified because of signing problems
			validationErrorSignatureInvalid => signature validation failed
			validationErrorExpired => exp validation failed
			validationErrorNotValidYet => nbf validation failed
			validationErrorIssuedAt => iat validation failed
	*/
	tokenClaims, err := jwt.ParseWithClaims(token, &models.Claims{}, func(token *jwt.Token) (i interface{}, err error) {
		return jwtSecret, nil
	})
	if err != nil {
		var message string
		if ve, ok := err.(*jwt.ValidationError); ok {
			// Handle different validation errors and set appropriate error messages.
			if ve.Errors&jwt.ValidationErrorMalformed != 0 {
				message = "token is malformed"
			} else if ve.Errors&jwt.ValidationErrorUnverifiable != 0 {
				message = "token could not be verified because of signing problems"
			} else if ve.Errors&jwt.ValidationErrorSignatureInvalid != 0 {
				message = "signature validation failed"
			} else if ve.Errors&jwt.ValidationErrorExpired != 0 {
				message = "token is expired"
			} else if ve.Errors&jwt.ValidationErrorNotValidYet != 0 {
				message = "token is not yet valid before sometime"
			} else {
				message = "can not handle this token"
			}
		}
		// Respond with an unauthorized status and the error message.
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": message,
		})
		c.Abort()
		return
	}

	// If the token is valid, extract claims and set them in the context.
	if claims, ok := tokenClaims.Claims.(*models.Claims); ok && tokenClaims.Valid {
		c.Set("loginType", claims.LoginType)
		c.Set("accountID", claims.AccountID)
		c.Set("isAdmin", claims.IsAdmin)
		c.Set("permissions", claims.Permissions)
		c.Set("expiresAt", claims.ExpiresAt)
		c.Next()
	} else {
		// If the token claims are not valid, abort the request.
		c.Abort()
		return
	}
}
