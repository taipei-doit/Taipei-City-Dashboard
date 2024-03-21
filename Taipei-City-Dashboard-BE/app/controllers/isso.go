package controllers

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/util"
	"TaipeiCityDashboardBE/global"
	"TaipeiCityDashboardBE/logs"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/lib/pq"
	"gorm.io/gorm"
)

/*
*** Note to External Developers ***

This file contains the controller functions for the Taipei Pass and Isso authentication methods.
We currently do not allow external developers to modify these methods, but you can use them as a reference.
*/

// AccessTokenResp ....
type respAccessToken struct {
	AccessToken  string `json:"access_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int64  `json:"expires_in"`
	RefreshToken string `json:"refresh_token"`
	Scope        string `json:"scope"`
}

type respAccessTokenWError struct {
	respAccessToken
	Error            string `json:"error"`
	ErrorDescription string `json:"error_description"`
}

type respUserInfo struct {
	Name         string `json:"name"`
	ReasonPhrase string `json:"reasonPhrase"`
	Status       int    `json:"status"`
	Data         struct {
		ID          string `json:"id"`
		Account     string `json:"account"`
		IDNo        string `json:"idNo"`
		VerifyLevel string `json:"verifyLevel"`
	} `json:"data"`
	Timestamp int64       `json:"timestamp"`
	Extra     interface{} `json:"extra"`
	Version   string      `json:"version"`
	HostNum   int         `json:"hostNum"`
}

// https://{taipeipass_url}/oauth/authorize?response_type=code&client_id={client_id}&scope={scopes}

func ExecIssoAuth(c *gin.Context) {
	var (
		accessToken   respAccessTokenWError
		userInfo      respUserInfo
		user          models.AuthUser
		respUserToken []byte
		respUserInfo  []byte
	)
	code := c.Query("code")
	logs.FInfo("isso login from %s code = %s", c.ClientIP(), code)

	if len(code) == 0 {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "code not exist"})
		return
	} else if len(code) == 6 {
		// Tapei Pass get token
		// ##Endpoint##  POST https://{taipeipass_url}/oauth/token
		// ## Header ##  Content-Type application/x-www-form-urlencoded
		// ##  Body  ##
		// *grant_type string 請填入 authorization_code
		// *client_id string {client_id}
		// *client_secret string {client_secret}
		// *code string 認證完成後所取得的 code 參數
		// ## Response ##  application/json
		// access_token string 呼叫 oauth api 用 token
		// token_type string access token 類型，通常為 bearer
		// refresh_token string 延展 access token 用 token
		// expires_in int access token 時效(秒)
		// scope string 此 access token 可取得的授權欄位
		// Response error:
		// {
		// 	"error": "invalid_grant",
		// 	"error_description": "Invalid authorization code: YTwPr5"
		// }
		urlGetToken := global.Isso.TaipeipassURL + "/oauth/token"
		body := "grant_type=authorization_code&client_id=" + global.Isso.ClientID + "&client_secret=" + global.Isso.ClientSecret + "&code=" + code
		// header
		headers := make(http.Header)
		headers.Add("Content-Type", "application/x-www-form-urlencoded")
		// get User Token
		respUserToken = HTTPClientRequest("POST", urlGetToken, body, headers)
		logs.FInfo("response User Token : %s", string(respUserToken))
		json.Unmarshal([]byte(respUserToken), &accessToken)

		// get user personal info
		// ## Endpoint ##
		// GET https://{taipeipass_url}/api/{version}/user/my
		// ## Header ##
		// Authorization Bearer {access token}
		urlGetUserInfo := global.Isso.TaipeipassURL + "/api/" + global.TaipeipassAPIVersion + "/user/my"
		// header
		headers.Add("Authorization", "Bearer "+accessToken.AccessToken)
		// get user info
		respUserInfo = HTTPClientRequest("GET", urlGetUserInfo, "", headers)
		json.Unmarshal([]byte(respUserInfo), &userInfo)
		idNoSHA := util.HashString(userInfo.Data.IDNo + global.IDNoSalt)

		// if isso user not Verifyed
		if userInfo.Data.VerifyLevel == "0" {
			c.JSON(http.StatusForbidden, gin.H{"error": "isso user not verifyed"})
			return
		}

		// create user if not exist
		if err := models.DBManager.Where("idno = ?", idNoSHA).First(&user).Error; err != nil {
			if errors.Is(err, gorm.ErrRecordNotFound) {

				user = models.AuthUser{
					Name:          userInfo.Data.Account,
					TpUuID:        &userInfo.Data.ID,
					TpAccount:     &userInfo.Data.Account,
					IDNo:          &idNoSHA,
					TpVerifyLevel: &userInfo.Data.VerifyLevel,
					LoginAt:       time.Now(),
				}
				// Attempt to create the new user in the database
				if err := models.DBManager.Create(&user).Error; err != nil {
					logs.FError("Failed to create user: %v", err)
					c.JSON(http.StatusUnauthorized, gin.H{"error": "unexpected database error"})
					return
				}
				// create user personal group
				personalGroupID, err := models.CreateGroup(userInfo.Data.Account+"'s group", true, user.ID)
				if err != nil {
					logs.FError("Failed to create user[%s] personal group:%s", userInfo.Data.Account, err)
				}
				// set user personal group permission
				// admin role id=1
				if err := models.CreateUserGroupRole(user.ID, personalGroupID, 1); err != nil {
					logs.FError("Failed to set userp[%s] personal group permission:%s", userInfo.Data.Account, err)
				}
				// create favorite dashboard
				tmpIndex := uuid.New().String()
				dashboardIndex := strings.Split(tmpIndex, "-")[0] + strings.Split(tmpIndex, "-")[1]
				dashboardName := "收藏組件"
				var dashboardComponents pq.Int64Array
				_, err = models.CreateDashboard(dashboardIndex, dashboardName, "favorite", dashboardComponents, personalGroupID)
				if err != nil {
					logs.FError("create user favorite dashboard failed %v", err)
				}

				logs.FInfo("create user success %d from IP[%s]", user.ID, c.ClientIP())
			} else {
				logs.FError("Login failed: unexpected database error: %v", err)
				c.JSON(http.StatusUnauthorized, gin.H{"error": "unexpected database error"})
				return
			}
		}

		// if user exist
		// check user is active
		if !*user.IsActive {
			logs.FInfo("isso_login_fail IP[%s] Err: User not activated %d", c.ClientIP(), user.ID)
			c.JSON(http.StatusForbidden, gin.H{"error": "User not activated"})
			return
		}

		permissions, err := models.GetUserPermission(user.ID)
		if err != nil {
			logs.FError("Failed to get user[%d] permission: %v", user.ID, err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "unexpected database error"})
			return
		}

		// generate JWT token
		user.LoginAt = time.Now()
		token, err := util.GenerateJWT(user.LoginAt.Add(global.TokenExpirationDuration), "Isso", user.ID, *user.IsAdmin, permissions)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": err.Error(),
			})
			return
		}

		// update last login time
		if err := models.DBManager.Save(&user).Error; err != nil {
			logs.FError("Failed to update login time: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "unexpected database error"})
			return
		}

		// return JWT token
		c.JSON(http.StatusOK, gin.H{
			"user":       user,
			"token":      token,
			"isso_token": accessToken.AccessToken,
		})

	} else if len(code) > 6 {
		// OAuth
		// ##Endpoint##  POST https://{isso_url}/oauth2/token
		// ## Header ##
		// Content-Type application/x-www-form-urlencoded
		// Authorization Basic {base64({clientId}:{client_secret})}
		// ##  Body  ##
		// *grant_type string 請填入 authorization_code
		// *code string 認證完成後所取得的 code 參數
		// ## Response：application/json ##
		// GET https://{isso_url}/oauth2/authorize?response_type=code&client_id={client_id}&scope={scopes}&state={state}
		// access_token string 呼叫 oauth api 用 token
		// token_type string access token 類型，通常為 bearer
		// refresh_token string 延展 access token 用 token (效期 60 分鐘)
		// expires_in int access token 時效(秒)
		// scope string 此 access token 可取得的授權欄位
		// accessUrl := global.IssoURL + "/oauth2/token?grant_type=authorization_code&code=" + code
		// credentialsString := global.IssoClientID + ":" + global.IssoClientSecret
		// encodedCredentials := base64.StdEncoding.EncodeToString([]byte(credentialsString))
		// headers := map[string]string{
		// 	"Authorization": "Basic " + encodedCredentials,
		// }
		// response = HTTPClientRequest(accessUrl, "POST", headers)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "authentication method not integrated yet"})
		return
	}

	if len(respUserInfo) == 0 {
		// return AccessTokenResp{}, user, fmt.Errorf("access token failed") , err.Error())
		logs.FInfo("isso_login_fail IP[%s] Err:%s", c.ClientIP(), accessToken.ErrorDescription)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "get access token faile"})
		return
	}
}

func IssoLogOut(c *gin.Context) {
	issoToken := c.Query("isso_token")

	headers := make(http.Header)
	headers.Add("Authorization", "Bearer "+issoToken)
	url := global.Isso.TaipeipassURL + "/oauth/logout"

	resp := HTTPClientRequest("POST", url, "", headers)
	logs.FInfo("isso logout. Response: %s", resp)
	c.JSON(http.StatusOK, gin.H{"status": "success"})
}

func HTTPClientRequest(method, url, payload string, headers http.Header) []byte {
	client := &http.Client{}
	req, err := http.NewRequest(method, url, strings.NewReader(payload))
	if err != nil {
		fmt.Println(err)
		return nil
	}

	// 設定自定義頭部
	req.Header = headers

	res, err := client.Do(req)
	if err != nil {
		fmt.Println(err)
		return nil
	}
	defer res.Body.Close()

	body, err := io.ReadAll(res.Body)
	if err != nil {
		fmt.Println(err)
		return nil
	}

	return body
}
