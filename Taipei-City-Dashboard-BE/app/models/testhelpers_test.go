package models

import (
	"fmt"
	"os"
	"testing"

	"TaipeiCityDashboardBE/global"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// initTestDB sets up DBDashboard for unit tests against the local dashboard database.
// Env vars override the defaults (host=127.0.0.1, port=5432, user=$USER, db=dashboard, no password, sslmode=disable).
func initTestDB(t *testing.T) {
	t.Helper()
	if DBDashboard != nil {
		return
	}
	cfg := global.DatabaseConfig{
		Host:     getTestEnv("DB_DASHBOARD_HOST", "127.0.0.1"),
		Port:     getTestEnv("DB_DASHBOARD_PORT", "5432"),
		User:     getTestEnv("DB_DASHBOARD_USER", os.Getenv("USER")),
		Password: getTestEnv("DB_DASHBOARD_PASSWORD", ""),
		DBName:   getTestEnv("DB_DASHBOARD_DBNAME", "dashboard"),
		SSLMode:  getTestEnv("DB_DASHBOARD_SSLMODE", "disable"),
	}
	dsn := fmt.Sprintf(
		"host=%s port=%s user=%s dbname=%s password=%s sslmode=%s",
		cfg.Host, cfg.Port, cfg.User, cfg.DBName, cfg.Password, cfg.SSLMode,
	)
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		t.Skipf("skip: cannot connect to test dashboard DB (%v)", err)
	}
	DBDashboard = db
}

func getTestEnv(key, fallback string) string {
	if v, ok := os.LookupEnv(key); ok {
		return v
	}
	return fallback
}
