// // Package controllers stores all the controllers for the Gin router.
package controllers

import (
	"TaipeiCityDashboardBE/app/models"
	"fmt"
	"html"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

func CreateChatLog(c *gin.Context) {
	var chatLog models.ChatLog
	
	accountID, exists  := c.Get("accountID")

	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"status": "error", "message": "Unauthorized"})
		return
	}

	// Sanitize input to prevent XSS
	session := c.PostForm("session")
	question := c.PostForm("question")
	answer := c.PostForm("answer")
    ipAddress := c.ClientIP()
	session = html.EscapeString(session)
	question = html.EscapeString(question)
	answer = html.EscapeString(answer)

	// Debugging: Print various headers to trace the client's IP address
	fmt.Println("remote_addr = ",        c.Request.RemoteAddr)
	fmt.Println("x_forwarded_for = ",    c.GetHeader("X-Forwarded-For"))
	fmt.Println("x_real_ip = ",          c.GetHeader("X-Real-IP"))
	fmt.Println("x_forwarded_proto = ",  c.GetHeader("X-Forwarded-Proto"))


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