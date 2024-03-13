// Package initial contains the functions to initialize the databases for the first time.
package initial

import (
	"fmt"
	"os"
	"os/exec"

	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/util"
	"TaipeiCityDashboardBE/global"
	"TaipeiCityDashboardBE/logs"
)

func InitDashboardManager() {
	initDashboardConfigs()
	addRoles()
	createAdmin()
}

// and executing an SQL file.
func initDashboardConfigs() {
	// Check if the "psql" command not exists
	err := checkPostgreSQLClient()
	if err != nil {
		logs.FError("Error checking PostgreSQL client: %s", err)
		return
	}

	// get import file path
	filePath := global.SampleDataDir + global.PostgresManagerSampleDataFile
	logs.FInfo("import file name: %s", filePath)
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		logs.FError("file %s not exist", filePath)
		return
	}

	err = executeSQLFile(global.PostgresManager,filePath)
	if err != nil {
		logs.FError("error executing SQL file: %s", err)
	}
}

func addRoles() {
	// create init roles[admin/editor/viewer]
	_, err := models.CreateRole("admin", true, true, true)
	if err != nil {
		logs.FError("Failed to create admin role:%s", err)
	}
	_, err = models.CreateRole("editor", false, true, true)
	if err != nil {
		logs.FError("Failed to create editor role:%s", err)
	}
	_, err = models.CreateRole("viewer", false, false, true)
	if err != nil {
		logs.FError("Failed to create viewer role:%s", err)
	}
}

func createAdmin() {
	userName := global.DashboardDefaultUserName
	email := global.DashboardDefaultUserEmail
	password := util.HashString(global.DashboardDefaultUserPassword)
	logs.FInfo("userName: %s", userName)
	logs.FInfo("user email: %s", email)

	// get public groupID
	publicGroupID, err := models.GetGroupIDByName("public")
	if err != nil {
		logs.FError("Failed to get public group:%s", err)
	}
	logs.FInfo("get public group id:%d", publicGroupID)

	// get admin roleID
	adminRoleID, err := models.GetRoleIDByName("admin")
	if err != nil {
		logs.FError("Failed to get admin role:%s", err)
	}
	logs.FInfo("get admin role id:%d", adminRoleID)

	// create admin user
	isAdmin := true
	isActive := true
	isWhitelist := true
	isBlacked := false

	adminUserID, err := models.CreateUser(userName, &email, &password, &isAdmin, &isActive, &isWhitelist, &isBlacked, nil)
	if err != nil {
		logs.FError("Failed to create user:%s", err)
	}
	logs.FInfo("create admin: %s success", userName)

	// set admin user permission(group:public, role:admin)
	if err := models.CreateUserGroupRole(adminUserID, publicGroupID, adminRoleID); err != nil {
		logs.FError("Failed to set admin permission:%s", err)
	}
}

func InitSampleCityData() {
	// Check if the "psql" command not exists
	err := checkPostgreSQLClient()
	if err != nil {
		logs.FError("Error checking PostgreSQL client: %s", err)
		return
	}

	// get import file path
	filePath := global.SampleDataDir + global.PostgresDashboardSampleDataFile
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		panic(fmt.Sprintf("file %s not exist", filePath))
	}
	logs.FInfo("import file name: %s", filePath)

	err = executeSQLFile(global.PostgresDashboard,filePath)
	if err != nil {
		logs.FError("error executing SQL file: %s", err)
	}
}

// Check if PostgreSQL client is installed
func checkPostgreSQLClient() error {
	_, err := exec.LookPath("psql")
	if err != nil {
		// Install PostgreSQL client
		cmd := exec.Command("apk", "add", "postgresql-client")
		err := cmd.Run()
		if err != nil {
			return fmt.Errorf("error installing PostgreSQL client: %s", err)
		}
	}
	return nil
}

// ExecuteSQLFile executes SQL file using psql
func executeSQLFile(dbConfig global.DatabaseConfig, filePath string) error {
	cmd := exec.Command("psql", "-h", dbConfig.Host, "-p", dbConfig.Port, "-U", dbConfig.User, "-d", dbConfig.DBName, "-f", filePath)
	// cmd.Stdin = strings.NewReader(dbConfig.Password + "\n")

	err := cmd.Run()
	if err != nil {
		return fmt.Errorf("error executing psql command: %s", err)
	}
	return nil
}