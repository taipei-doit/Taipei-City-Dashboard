package models

import (
	"strings"
	"time"
)

/* ----- Models ----- */

type Issue struct {
	ID           int64     `json:"id" gorm:"column:id;autoincrement;primaryKey"`
	Title        string    `json:"title" gorm:"column:title;type:varchar;not null"`
	UserName     string    `json:"user_name" gorm:"column:user_name;type:varchar;not null"`
	UserID       string    `json:"user_id" gorm:"column:user_id;type:varchar;not null"`
	Context      string    `json:"context" gorm:"column:context;type:text"`
	Description  string    `json:"description" gorm:"column:description;type:text;not null"`
	DecisionDesc string    `json:"decision_desc" gorm:"column:decision_desc;type:text"`
	Status       string    `json:"status" gorm:"column:status;type:varchar;not null"`
	UpdatedBy    string    `json:"updated_by" gorm:"column:updated_by;type:varchar;not null"`
	CreatedAt    time.Time `json:"created_at" gorm:"column:created_at;type:timestamp with time zone;not null"`
	UpdatedAt    time.Time `json:"updated_at" gorm:"column:updated_at;type:timestamp with time zone;not null"`
}

/* ----- Handlers ----- */

func GetAllIssues(pageSize int, pageNum int, filterByStatus string, sort string, order string) (issues []Issue, totalIssues int64, resultNum int64, err error) {
	tempDB := DBManager.Table("issues")

	// Count the total amount of issues
	tempDB.Count(&totalIssues)

	// Filter by status
	if filterByStatus != "" {
		statuses := strings.Split(filterByStatus, ",")
		tempDB = tempDB.Where("issues.status IN (?)", statuses)
	}

	tempDB.Count(&resultNum)

	// Sort the issues
	if sort != "" {
		tempDB = tempDB.Order("issues." + sort + " " + order)
	}

	// Paginate the issues
	if pageSize > 0 {
		tempDB = tempDB.Limit(pageSize)
		if pageNum > 0 {
			tempDB = tempDB.Offset((pageNum - 1) * pageSize)
		}
	}

	// Get the issues
	err = tempDB.Find(&issues).Error

	return issues, totalIssues, resultNum, err
}

func CreateIssue(title string, userName string, userID string, context string, description string) (issue Issue, err error) {
	issue.CreatedAt = time.Now()
	issue.UpdatedAt = time.Now()
	issue.Status = "待處理"
	issue.Title = title
	issue.UserName = userName
	issue.UserID = userID
	issue.Context = context
	issue.Description = description

	err = DBManager.Create(&issue).Error
	return issue, err
}

func UpdateIssueByID(id string, status string, descisionDesc string, updatedBy string) (issue Issue, err error) {
	issue.UpdatedAt = time.Now()
	issue.Status = status
	issue.DecisionDesc = descisionDesc
	issue.UpdatedBy = updatedBy

	err = DBManager.Table("issues").Where("id = ?", id).Updates(&issue).Error
	return issue, err
}
