package middleware

import (
	"fmt"
	"net/http"
	"time"

	"TaipeiCityDashboardBE/app/cache"

	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis"
)

func LimitAPIRequests(limit int, timeframe time.Duration) gin.HandlerFunc {
	return func(c *gin.Context) {
		currentTime := time.Now().UnixNano()
		var userIdentifier string
		user := c.GetString("user")

		if user != "" {
			userIdentifier = user
		} else {
			userIdentifier = c.ClientIP()
		}

		redisKey := fmt.Sprint("User:", userIdentifier, ":", c.Request.Method, ":", c.Request.RequestURI)

		// Remove any old records
		_, err := cache.Redis.ZRemRangeByScore(redisKey, "0", fmt.Sprint(currentTime-timeframe.Nanoseconds())).Result()
		if err != nil {
			c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"status": "error", "message": "Error removing old records from Redis"})
		}
		// Count the number of remaining records
		reqs, err := cache.Redis.ZRange(redisKey, 0, -1).Result()
		if err != nil {
			c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"status": "error", "message": "Error counting past requests from Redis"})
		}
		// If the number of records is greater than the limit, abort the request
		if len(reqs) >= limit {
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{"status": "error", "message": "Too many requests on the same API. Try again later"})
			return
		}

		c.Next()

		// Add the current request to the list of requests
		cache.Redis.ZAddNX(redisKey, redis.Z{Score: float64(currentTime), Member: currentTime})
		cache.Redis.Expire(redisKey, timeframe)
	}
}

func LimitTotalRequests(limit int, timeframe time.Duration) gin.HandlerFunc {
	return func(c *gin.Context) {
		currentTime := time.Now().UnixNano()
		var userIdentifier string
		user := c.GetString("user")

		if user != "" {
			userIdentifier = user
		} else {
			userIdentifier = c.ClientIP()
		}

		// TO BE COMPLETED: check if white_listed or black_listed and skip if so

		redisKey := fmt.Sprint("User_Total:", userIdentifier)

		// Remove any old records
		_, err := cache.Redis.ZRemRangeByScore(redisKey, "0", fmt.Sprint(currentTime-timeframe.Nanoseconds())).Result()
		if err != nil {
			c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"status": "error", "message": "Error removing old records from Redis"})
		}
		// Count the number of remaining records
		reqs, err := cache.Redis.ZRange(redisKey, 0, -1).Result()
		if err != nil {
			c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"status": "error", "message": "Error counting past requests from Redis"})
		}
		// If the number of records is greater than the limit, abort the request
		if len(reqs) >= limit {
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{"status": "error", "message": "Too many requests. Try again later"})
			return
		}

		c.Next()

		// Add the current request to the list of requests
		cache.Redis.ZAddNX(redisKey, redis.Z{Score: float64(currentTime), Member: currentTime})
		cache.Redis.Expire(redisKey, timeframe)
	}
}
