package controllers

import (
	"TaipeiCityDashboardBE/app/services"
	"net/http"

	"github.com/gin-gonic/gin"
)

/*
TriggerQdrantRebuild is a test endpoint to manually trigger the Qdrant rebuild process.
POST /api/v1/qdrant/rebuild
*/
func TriggerQdrantRebuild(c *gin.Context) {
    // 同步執行，並取得回傳的資料
    data, err := services.RebuildQdrantPublicCollection()
    if err != nil {
        // 如果是「正在重建中」的錯誤，回傳 409 Conflict 會更語意化
        if err.Error() == "qdrant rebuild is already in progress" {
            c.JSON(http.StatusConflict, gin.H{"status": "error", "message": err.Error()})
            return
        }
        c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
        return
    }

    c.JSON(http.StatusOK, gin.H{
        "status":  "success",
        "message": "Synchronous rebuild complete (up to implemented steps).",
        "data":    data,
    })
}