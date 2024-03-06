package auth

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"TaipeiCityDashboardBE/app/database"
	"TaipeiCityDashboardBE/app/database/models"
	"TaipeiCityDashboardBE/global"
	"TaipeiCityDashboardBE/logs"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

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
		urlGetToken := global.TaipeipassURL + "/oauth/token"
		body := "grant_type=authorization_code&client_id=" + global.IssoClientID + "&client_secret=" + global.IssoClientSecret + "&code=" + code
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
		urlGetUserInfo := global.TaipeipassURL + "/api/" + global.TaipeipassAPIVersion + "/user/my"
		// header
		headers.Add("Authorization", "Bearer "+accessToken.AccessToken)
		// get user info
		respUserInfo = HTTPClientRequest("GET", urlGetUserInfo, "", headers)
		json.Unmarshal([]byte(respUserInfo), &userInfo)
		idNoSHA := HashString(userInfo.Data.IDNo)

		// if isso user not Verifyed
		if userInfo.Data.VerifyLevel == "0" {
			c.JSON(http.StatusForbidden, gin.H{"error": "isso user not verifyed"})
			return
		}

		// create user if not exist
		if err := database.DBManager.Where("idno = ?", idNoSHA).First(&user).Error; err != nil {
			if errors.Is(err, gorm.ErrRecordNotFound) {

				user = models.AuthUser{
					TpUuid:        &userInfo.Data.ID,
					TpAccount:     &userInfo.Data.Account,
					IdNo:          &idNoSHA,
					TpVerifyLevel: &userInfo.Data.VerifyLevel,
					LoginAt:       time.Now(),
				}
				// Attempt to create the new user in the database
				if err := database.DBManager.Create(&user).Error; err != nil {
					logs.FError("Failed to create user: %v", err)
					c.JSON(http.StatusUnauthorized, gin.H{"error": "unexpected database error"})
					return
				}
				// create user personal group
				personalGroupID, err := CreateGroup(userInfo.Data.Account+"'s group", true, user.Id)
				if err != nil {
					logs.FError("Failed to create user[%s] personal group:%s", userInfo.Data.Account, err)
				}
				// set user personal group permission
				// admin role id=1
				if err := CreateUserGroupRole(user.Id, personalGroupID, 1); err != nil {
					logs.FError("Failed to set userp[%s] personal group permission:%s", userInfo.Data.Account, err)
				}
				logs.FInfo("create user success %d from IP[%s]", user.Id, c.ClientIP())
			} else {
				logs.FError("Login failed: unexpected database error: %v", err)
				c.JSON(http.StatusUnauthorized, gin.H{"error": "unexpected database error"})
				return
			}
		}

		// if user exist
		// check user is active
		if !user.IsActive {
			logs.FInfo("isso_login_fail IP[%s] Err: User not activated %d", c.ClientIP(), user.Id)
			c.JSON(http.StatusForbidden, gin.H{"error": "User not activated"})
			return
		}

		permissions, err := GetUserPermission(user.Id)

		// generate JWT token
		user.LoginAt = time.Now()
		token, err := GenerateJWT(user.LoginAt, "Isso", user.Id, user.IsAdmin, permissions)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": err.Error(),
			})
			return
		}

		// update last login time
		if err := database.DBManager.Save(&user).Error; err != nil {
			logs.FError("Failed to update login time: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "unexpected database error"})
			return
		}

		// return JWT token
		c.JSON(http.StatusOK, gin.H{
			"user":  user,
			"token": token,
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
