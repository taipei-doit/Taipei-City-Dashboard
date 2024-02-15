package initial

import (
	"os"

	"TaipeiCityDashboardBE/internal/auth"
	"TaipeiCityDashboardBE/logs"
)

func InitDashboardManager() {
	initPermission()
	initManagerData()
}

func initPermission() {
	userName := os.Getenv("DASHBOARD_DEFAULT_USERNAME")
	email := os.Getenv("DASHBOARD_DEFAULT_Email")
	password := auth.HashString(os.Getenv("DASHBOARD_DEFAULT_PASSWORD"))

	// create init user
	adminUserID, err := auth.CreateUser(userName, &email, &password, true, true, true, false, nil)
	if err != nil {
		logs.FError("Failed to create user:%s", err)
	}
	// create first group public
	publicGroupID, err := auth.CreateGroup("public", false, adminUserID)
	if err != nil {
		logs.FError("Failed to create public group:%s", err)
	}
	// create init roles[admin/editor/viewer]
	adminRoleID, err := auth.CreateRole("admin", true, true, true)
	if err != nil {
		logs.FError("Failed to create admin role:%s", err)
	}
	_, err = auth.CreateRole("editor", false, true, true)
	if err != nil {
		logs.FError("Failed to create editor role:%s", err)
	}
	_, err = auth.CreateRole("viewer", false, false, true)
	if err != nil {
		logs.FError("Failed to create viewer role:%s", err)
	}
	// set admin permission
	if err := auth.CreateUserGroupRole(adminUserID, publicGroupID, adminRoleID); err != nil {
		logs.FError("Failed to set admin permission:%s", err)
	}
	// create admin personal group
	personalGroupID, err := auth.CreateGroup(userName+"'s group", true, adminUserID)
	if err != nil {
		logs.FError("Failed to create admin personal group:%s", err)
	}
	// set admin personal group permission
	if err := auth.CreateUserGroupRole(adminUserID, personalGroupID, adminRoleID); err != nil {
		logs.FError("Failed to set admin personal group permission:%s", err)
	}
}

func initManagerData() {}

func InitSampleCityData() {}
