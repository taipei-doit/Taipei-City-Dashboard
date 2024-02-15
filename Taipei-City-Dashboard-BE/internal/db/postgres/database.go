// Package postgres initiates the connections to the two postgreSQL databases of this application.
package postgres

import (
	"crypto/sha256"
	"fmt"
	"os"
	"time"

	"TaipeiCityDashboardBE/internal/db/postgres/models"
	"TaipeiCityDashboardBE/logs"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// DBDashboard stores the actual statistical data for each component in the dashboard.
// DBManager stores the user data and various configs for this application.

// Global Variables that allow access to the DB anywhere in the application.
var (
	DBDashboard *gorm.DB
	DBManager   *gorm.DB
)

// ConnectToDatabases connects to the two postgreSQL databases of this application.
func ConnectToDatabases(dbNames ...interface{}) {
	for _, dbName := range dbNames {
		if dbString, ok := dbName.(string); ok {
			conn := ConnectToDatabase(dbString)
			// Switch statement to handle different database names.
			switch dbString {
			case "DASHBOARD":
				DBDashboard = conn
			case "MANAGER":
				DBManager = conn
			default:
				panic("DB does not in connection list.")
			}
		}
	}
}

// ConnectToDatabase establishes a connection to the specified database using the provided dbName.
// It constructs the database connection string by fetching environment variables for host, port, user, dbname, and password.
// The connection string is formatted as "host=... port=... user=... dbname=... password=... sslmode=disable".
// The function returns a pointer to a gorm.DB (database connection) and logs success or failure messages accordingly.
func ConnectToDatabase(dbName string) *gorm.DB {
	// Constructing the database connection string using environment variables
	dbargs := fmt.Sprintf(
		"host=%s port=%s user=%s dbname=%s password=%s sslmode=disable",
		os.Getenv(fmt.Sprintf("DB_%s_HOST", dbName)),
		os.Getenv(fmt.Sprintf("DB_%s_PORT", dbName)),
		os.Getenv(fmt.Sprintf("DB_%s_USER", dbName)),
		os.Getenv(fmt.Sprintf("DB_%s_DBNAME", dbName)),
		os.Getenv(fmt.Sprintf("DB_%s_PASSWORD", dbName)),
	)

	// Establish a connection to the database using gorm.Open and the constructed connection string
	dbConn, err := gorm.Open(postgres.Open(dbargs), &gorm.Config{})
	if err != nil {
		// Log an error and panic if there is an issue connecting to the database
		logs.FError("Error connecting to %s database", dbName)
		panic("Connecting to database error")
	}

	// Log a success message if the connection is established successfully
	logs.FInfo("%s database connecting", dbName)
	return dbConn
}

// CloseConnects closes the connections to the specified databases.
// It takes a variable number of database names and closes the corresponding connections.
func CloseConnects(dbNames ...interface{}) {
	for _, dbName := range dbNames {
		if dbString, ok := dbName.(string); ok {
			// Switch statement to handle different database names.
			switch dbString {
			case "DASHBOARD":
				CloseConnect(dbString, DBDashboard)
			case "MANAGER":
				CloseConnect(dbString, DBManager)
			default:
				panic("DB does not in connection list.")
			}
		}
	}
}

// CloseConnect closes the connection to the specified database.
// It takes the database name and the corresponding *gorm.DB object as parameters.
func CloseConnect(dbName string, DB *gorm.DB) {
	// Retrieve the underlying SQL database connection.
	sqlDB, err := DB.DB()
	if err != nil {
		logs.FError("failed to get %s database connection", dbName)
	}

	// Close the underlying SQL database connection.
	if err := sqlDB.Close(); err != nil {
		logs.FError("failed to close %s database connection", dbName)
	} else {
		logs.FInfo("%s database connection closed", dbName)
	}
}

func MigrateManagerSchema() {
	// Retrieve the underlying SQL database connection.
	if DBManager != nil {
		DBManager.AutoMigrate(&models.EmailUser{}, &models.IssoUser{}, &models.Role{}, &models.Group{})
		DBManager.AutoMigrate(&models.EmailUserRole{}, &models.EmailUserGroup{})
		DBManager.AutoMigrate(&models.IssoUserRole{}, &models.IssoUserGroup{})
		DBManager.AutoMigrate(&models.Component{}, &models.ComponentChart{}, &models.ComponentMap{})
		DBManager.AutoMigrate(&models.Dashboard{}, &models.DashboardGroup{}, &models.Issue{})

		// All users beneath the public group do not need to be added to the public group
		DBManager.Exec("ALTER TABLE email_user_groups ADD CONSTRAINT check_group_id CHECK (group_id > 1);")
		DBManager.Exec("ALTER TABLE isso_user_groups ADD CONSTRAINT check_group_id CHECK (group_id > 1);")
		// create user is temp
		createUser()
	} else {
		panic("failed to get Manager database connection")
	}
}

func createUser() {
	h := sha256.New()
	h.Write([]byte("TUIC"))
	pass := fmt.Sprintf("%x", h.Sum(nil))
	userToAdd := models.EmailUser{
		Email:    "tuic@gov.taipei",
		Name:     "Taipei",
		Password: pass,
		// ... 其他欄位
		CreatedAt: time.Now(),
		// LoginAt:   time.Now(),
	}
	resultU := DBManager.Create(&userToAdd)
	if resultU.Error != nil {
		logs.FError("發生錯誤：%v", resultU.Error)
	}

	rolesToAdd := []models.Role{
		{Name: "admin"},
		{Name: "editor"},
		{Name: "viewer"},
	}
	resultR := DBManager.Create(&rolesToAdd)
	if resultR.Error != nil {
		logs.FError("發生錯誤：%v", resultR.Error)
	}

	groupsToAdd := []models.Group{
		{Name: "public"}, // all user beline public group
		{Name: "employee"},
	}
	resultG := DBManager.Create(&groupsToAdd)
	if resultG.Error != nil {
		logs.FError("發生錯誤：%v", resultG.Error)
	}
	emailUserRolesToAdd := []models.EmailUserRole{
		{UserID: 1, RoleID: 1},
		{UserID: 1, RoleID: 2},
	}
	resultER := DBManager.Create(&emailUserRolesToAdd)
	if resultER.Error != nil {
		logs.FError("發生錯誤：%v", resultER.Error)
	}

	emailUserGroupsToAdd := []models.EmailUserGroup{
		{UserID: 1, GroupID: 2},
	}
	resultEG := DBManager.Create(&emailUserGroupsToAdd)
	if resultEG.Error != nil {
		logs.FError("發生錯誤：%v", resultEG.Error)
	}
}
