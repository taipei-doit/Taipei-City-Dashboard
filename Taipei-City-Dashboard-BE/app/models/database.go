// Package models initiates the connections to the two postgreSQL databases of this application and stores models and handlers.
package models

import (
	"bufio"
	"database/sql"
	"fmt"
	"os"
	"strings"

	"TaipeiCityDashboardBE/global"
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

// ConnectToDatabases connects to the two PostgreSQL databases used by this application.
// It accepts a variable number of database names as arguments and establishes connections to each specified database.
// The function iterates over the provided database names and connects to the corresponding databases.
// It uses a switch statement to handle different database names and assigns the database connections accordingly.
func ConnectToDatabases(dbNames ...interface{}) {
	for _, dbName := range dbNames {
		if dbString, ok := dbName.(string); ok {
			// Switch statement to handle different database names.
			switch dbString {
			case "DASHBOARD":
				logs.FInfo("DASHBOARD Hostname: %s", global.PostgresDashboard.Host)
				DBDashboard = ConnectToDatabase(global.PostgresDashboard)
			case "MANAGER":
				logs.FInfo("MANAGER Hostname: %s", global.PostgresManager.Host)
				DBManager = ConnectToDatabase(global.PostgresManager)
			default:
				panic("Database not in connection list.")
			}
		}
	}
}

// ConnectToDatabase establishes a connection to the specified database using the provided DatabaseConfig.
// It constructs the database connection string using the provided database configuration and establishes a connection using gorm.Open.
// The function returns a pointer to a gorm.DB (database connection) and logs success or failure messages accordingly.
func ConnectToDatabase(dbConfig global.DatabaseConfig) *gorm.DB {
	// Constructing the database connection string using database configuration
	dbargs := fmt.Sprintf(
		"host=%s port=%s user=%s dbname=%s password=%s sslmode=disable",
		dbConfig.Host,
		dbConfig.Port,
		dbConfig.User,
		dbConfig.DBName,
		dbConfig.Password,
	)

	// Establish a connection to the database using gorm.Open and the constructed connection string
	dbConn, err := gorm.Open(postgres.Open(dbargs), &gorm.Config{})
	if err != nil {
		// Log an error and panic if there is an issue connecting to the database
		logs.FError("Error connecting to %s database", dbConfig.Host)
		panic("Connecting to database error")
	}

	// Log a success message if the connection is established successfully
	logs.FInfo("%s database connected", dbConfig.Host)
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
		DBManager.AutoMigrate(&AuthUser{}, &Role{}, &Group{})
		DBManager.AutoMigrate(&AuthUserGroupRole{})
		DBManager.AutoMigrate(&Component{}, &ComponentChart{}, &ComponentMap{})
		DBManager.AutoMigrate(&Dashboard{}, &DashboardGroup{}, &Issue{})

		// All users beneath the public group do not need to be added to the public group
		// DBManager.Exec("ALTER TABLE auth_user_group_roles ADD CONSTRAINT check_group_id CHECK (group_id > 1);")
		// DBManager.Exec("ALTER TABLE isso_user_groups ADD CONSTRAINT check_group_id CHECK (group_id > 1);")
	} else {
		panic("failed to get Manager database connection")
	}
}

// ExecuteSQLFile executes SQL statements from a given file.
func ExecuteSQLFile(db *sql.DB, filename string) error {
	// Open the SQL file
	file, err := os.Open(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	// Create a scanner to read the file line by line
	scanner := bufio.NewScanner(file)

	// Start a transaction
	tx, err := db.Begin()
	if err != nil {
		return err
	}

	// Iterate through the file line by line
	for scanner.Scan() {
		// Get the current line
		line := scanner.Text()

		// Skip comments and empty lines
		if strings.HasPrefix(line, "--") || line == "" {
			continue
		}

		// Execute the SQL statement
		_, err := tx.Exec(line)
		if err != nil {
			// Rollback the transaction if an error occurs
			tx.Rollback()
			logs.FError(err.Error())
		}
	}

	// Commit the transaction if all statements executed successfully
	if err := tx.Commit(); err != nil {
		return err
	}

	return nil
}
