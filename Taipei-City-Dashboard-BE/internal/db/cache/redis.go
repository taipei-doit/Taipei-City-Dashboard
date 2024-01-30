// Package cache initiates the connection to the redis database of this application.
package cache

import (
	"fmt"
	"os"
	"strconv"

	"TaipeiCityDashboardBE/logs"

	"github.com/go-redis/redis"
)

// Global Variables that allow access to the Redis anywhere in the application.
var Redis *redis.Client

// ConnectToRedis connects to the redis database of this application.
func ConnectToRedis() {
	db, _ := strconv.Atoi(os.Getenv("REDIS_DB"))

	Redis = redis.NewClient(&redis.Options{
		Addr:     os.Getenv("REDIS_ADDR"),
		Password: os.Getenv("REDIS_PASSWORD"),
		DB:       db,
	})

	// Check if connection is successful
	_, err := Redis.Ping().Result()
	if err != nil {
		panic(fmt.Sprint("Error connecting to Redis:", err.Error()))
	}
	logs.Info("Redis connected")
}

// CloseConnect closes the connection to the Redis database.
func CloseConnect() {
	Redis.Close()
	logs.Info("Redis connection closed")
}
