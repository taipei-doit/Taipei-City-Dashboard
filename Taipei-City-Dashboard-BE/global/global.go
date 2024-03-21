package global

import (
	"TaipeiCityDashboardBE/logs"
	"os"
	"strconv"
)

// IssoConfig defines the structure for Isso configuration
type IssoConfig struct {
	IssoURL           string
	TaipeipassURL     string
	ClientID      string
	ClientSecret  string
}

// DatabaseConfig defines the structure for database configuration
type DatabaseConfig struct {
	Host     string
	Port     string
	User     string
	Password string
	DBName   string
}

// RedisConfig defines the structure for Redis configuration
type RedisConfig struct {
	Addr     string
	Port     string
	Password string
	DB       int
}

var (
	JwtSecret = getEnv("JWT_SECRET","")
	IDNoSalt = getEnv("IDNO_SALT","")
	// gin addr
    GinAddr = getEnv("GIN_DOMAIN","") + ":" + getEnv("GIN_PORT", "8080")

	// Retrieve default user information for the dashboard; only necessary in the init function.
	DashboardDefaultUserName = getEnv("DASHBOARD_DEFAULT_USERNAME", "")
	DashboardDefaultUserEmail = getEnv("DASHBOARD_DEFAULT_Email", "")
	DashboardDefaultUserPassword = getEnv("DASHBOARD_DEFAULT_PASSWORD", "")

	// PostgresManager defines the configuration for the manager database
	PostgresManager = DatabaseConfig{
		Host:     getEnv("DB_MANAGER_HOST", "postgres-manager"),
		Port:     getEnv("DB_MANAGER_PORT", "5432"),
		User:     getEnv("DB_MANAGER_USER", ""),
		Password: getEnv("DB_MANAGER_PASSWORD", ""),
		DBName:   getEnv("DB_MANAGER_DBNAME", "dashboardmanager"),
	}

	// PostgresDashboard defines the configuration for the dashboard database
	PostgresDashboard = DatabaseConfig{
		Host:     getEnv("DB_DASHBOARD_HOST", "postgres-data"),
		Port:     getEnv("DB_DASHBOARD_PORT", "5432"),
		User:     getEnv("DB_DASHBOARD_USER", ""),
		Password: getEnv("DB_DASHBOARD_PASSWORD", ""),
		DBName:   getEnv("DB_DASHBOARD_DBNAME", "dashboard"),
	}

	// only used in the init function.
	PostgresManagerSampleDataFile = getEnv("MANAGER_SAMPLE_FILE", "dashboardmanager-demo.sql")
    PostgresDashboardSampleDataFile = getEnv("DASHBOARD_SAMPLE_FILE", "dashboard-demo.sql")

	Isso = IssoConfig{
		IssoURL:          getEnv("ISSO_URL", "https://id.taipei/isso"),
		TaipeipassURL:    getEnv("TAIPEIPASS_URL", "https://id.taipei/tpcd"),
		ClientID:     getEnv("ISSO_CLIENT_ID", ""),
		ClientSecret: getEnv("ISSO_CLIENT_SECRET", ""),
	}

	Redis = RedisConfig{
		Addr:     getEnv("REDIS_ADDR", "redis"),
		Port:     getEnv("REDIS_PORT", "6379"),
		Password: getEnv("REDIS_PASSWORD", ""),
		DB:       getIntEnv("REDIS_DB", 0),
	}
)

func init() {
	logs.FInfo(PostgresDashboard.Host)
	
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

func getIntEnv(key string, fallback int) int {
	if valueStr, ok := os.LookupEnv(key); ok {
		value, err := strconv.Atoi(valueStr)
		if err != nil {
			return fallback
		}
		return value
	}
	return fallback
}
