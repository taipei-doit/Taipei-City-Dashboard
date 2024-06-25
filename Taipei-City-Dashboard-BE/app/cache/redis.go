// Package cache initiates the connection to the redis database of this application.
/*
Developed By Taipei Urban Intelligence Center 2023-2024

// Lead Developer:  Igor Ho (Full Stack Engineer)
// Systems & Auth: Ann Shih (Systems Engineer)
// Data Pipelines:  Iima Yu (Data Scientist)
// Design and UX: Roy Lin (Prev. Consultant), Chu Chen (Researcher)
// Testing: Jack Huang (Data Scientist), Ian Huang (Data Analysis Intern)
*/
package cache

import (
	"fmt"

	"TaipeiCityDashboardBE/global"
	"TaipeiCityDashboardBE/logs"

	"github.com/go-redis/redis"
)

// Redis is a variable that allow access to the Redis anywhere in the application.
var Redis *redis.Client

// ConnectToRedis connects to the redis database of this application.
func ConnectToRedis() {
	Redis = redis.NewClient(&redis.Options{
		Addr:     global.Redis.Host + ":" + global.Redis.Port,
		Password: global.Redis.Password,
		DB:       global.Redis.DB,
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
