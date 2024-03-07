// Package initial contains the functions to initialize the databases for the first time.
package initial

import (
	"os"
	"os/exec"

	"TaipeiCityDashboardBE/app/models"
	"TaipeiCityDashboardBE/app/util"
	"TaipeiCityDashboardBE/logs"
)

func InitDashboardManager() {
	initDashboards()
	addRoles()
	createAdmin()
}

// and executing an SQL file.
func initDashboards() {
	// Set the command and parameters to install the PostgreSQL client
	cmdInstallPsql := exec.Command("apk", "add", "postgresql-client")
	// Execute the command to install the PostgreSQL client
	if err := cmdInstallPsql.Run(); err != nil {
		logs.FError("Error installing PostgreSQL client:%s", err)
		return
	}

	// Set the command and parameters to execute the SQL file using psql
	cmdPsql := exec.Command("psql", "-h", os.Getenv("DB_MANAGER_HOST"), "-U", os.Getenv("DB_MANAGER_USER"), "-d", os.Getenv("DB_MANAGER_DBNAME"), "-f", "/opt/db-sample-data/dashboardmanager-demo.sql")

	// Create a pipe to pass the password to psql command
	cmdStdin, err := cmdPsql.StdinPipe()
	if err != nil {
		logs.FError("Error creating pipe to psql command: %s", err)
	}

	// Start the command
	err = cmdPsql.Start()
	if err != nil {
		logs.FError("Error starting psql command: %s", err)
	}

	// Write the password to the psql command's standard input
	_, err = cmdStdin.Write([]byte(os.Getenv("DB_MANAGER_PASSWORD") + "\n"))
	if err != nil {
		logs.FError("Error writing password to psql command: %s", err)
	}

	// Close the standard input of the psql command
	err = cmdStdin.Close()
	if err != nil {
		logs.FError("Error closing standard input of psql command: %s", err)
	}

	// Wait for the command to finish
	err = cmdPsql.Wait()
	if err != nil {
		logs.FError("Error executing psql command: %s", err)
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
	userName := os.Getenv("DASHBOARD_DEFAULT_USERNAME")
	email := os.Getenv("DASHBOARD_DEFAULT_Email")
	password := util.HashString(os.Getenv("DASHBOARD_DEFAULT_PASSWORD"))
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
	// Set the command and parameters to install the PostgreSQL client
	cmdInstallPsql := exec.Command("apk", "add", "postgresql-client")
	// Execute the command to install the PostgreSQL client
	if err := cmdInstallPsql.Run(); err != nil {
		logs.FError("Error installing PostgreSQL client:%s", err)
		return
	}

	// Set the command and parameters to execute the SQL file using psql
	cmdPsql := exec.Command("psql", "-h", os.Getenv("DB_DASHBOARD_HOST"), "-U", os.Getenv("DB_DASHBOARD_USER"), "-d", os.Getenv("DB_DASHBOARD_DBNAME"), "-f", "/opt/db-sample-data/dashboard-demo.sql")

	// Create a pipe to pass the password to psql command
	cmdStdin, err := cmdPsql.StdinPipe()
	if err != nil {
		logs.FError("Error creating pipe to psql command: %s", err)
	}

	// Start the command
	err = cmdPsql.Start()
	if err != nil {
		logs.FError("Error starting psql command: %s", err)
	}

	// Write the password to the psql command's standard input
	_, err = cmdStdin.Write([]byte(os.Getenv("DB_DASHBOARD_PASSWORD") + "\n"))
	if err != nil {
		logs.FError("Error writing password to psql command: %s", err)
	}

	// Close the standard input of the psql command
	err = cmdStdin.Close()
	if err != nil {
		logs.FError("Error closing standard input of psql command: %s", err)
	}

	// Wait for the command to finish
	err = cmdPsql.Wait()
	if err != nil {
		logs.FError("Error executing psql command: %s", err)
	}
}
