// // Package controllers stores all the controllers for the Gin router.
package controllers

import (
	"TaipeiCityDashboardBE/app/models"
	"html"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

type CreateChatLogReq struct {
	Session  string `json:"session" form:"session"`
	Question string `json:"question" form:"question"`
	Answer   string `json:"answer" form:"answer"`
}

func CreateChatLog(c *gin.Context) {
	var chatLog models.ChatLog

	accountID, exists := c.Get("accountID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"status": "error", "message": "Unauthorized"})
		return
	}

	var req CreateChatLogReq
	if err := c.ShouldBind(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// Sanitize input to prevent XSS
	session := html.EscapeString(req.Session)
	question := html.EscapeString(req.Question)
	answer := html.EscapeString(req.Answer)
	ipAddress := c.ClientIP()

	chatLog, _ = models.CreateChatLog(session, question, answer, ipAddress, accountID.(int))
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": chatLog})
}

func GetALLChatLog(c *gin.Context) {
	var chatLogList []models.ChatLog
	
	accountID, exists  := c.Get("accountID")

	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"status": "error", "message": "Unauthorized"})
		return
	}

	chatLogList, _ = models.GetALLChatLogSession(accountID.(int))

	type ChatLogSummary struct {
		Session   string    `json:"session"`		
		CreatedAt time.Time `json:"created_at"`
	}

    var summaries []ChatLogSummary
    for _, log := range chatLogList {
        summaries = append(summaries, ChatLogSummary{
            Session:   log.Session,
            CreatedAt: log.CreatedAt,
        })
    }

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": summaries})
}

func GetChatLogDetailBySession(c *gin.Context) {

	var chatLogList []models.ChatLog
	session := c.Param("session")
	session = html.EscapeString(session)
	accountID, exists  := c.Get("accountID")

	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"status": "error", "message": "Unauthorized"})
		return
	}

	chatLogList, _ = models.GetChatLogDetailBySession(session,accountID.(int))
	c.JSON(http.StatusOK, gin.H{"status": "success", "data": chatLogList})
}