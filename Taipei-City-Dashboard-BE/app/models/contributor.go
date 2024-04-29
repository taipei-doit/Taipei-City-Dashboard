package models

import (
	"time"
)

/* ----- Models ----- */

type Contributor struct {
	ID           int64     `json:"id" gorm:"column:id;autoincrement;primaryKey"`
	UserID       string    `json:"user_id" gorm:"column:user_id;type:varchar;not null"`
	UserName     string    `json:"user_name" gorm:"column:user_name;type:varchar;not null"`
	Image        string    `json:"image" gorm:"column:image;type:text"`
	Link         string    `json:"link" gorm:"column:link;type:text;not null"`
	Status       int64     `json:"status" gorm:"column:status;type:int;not null"`
	CreatedAt    time.Time `json:"created_at" gorm:"column:created_at;type:timestamp with time zone;not null"`
	UpdatedAt    time.Time `json:"updated_at" gorm:"column:updated_at;type:timestamp with time zone;not null"`
}

/* ----- Handlers ----- */

func GetAllContributors(pageSize int, pageNum int, filterByStatus int, sort string, order string) (contributors []Contributor, totalContributors int64, resultNum int64, err error) {
	tempDB := DBManager.Table("contributors")

	// Count the total amount of contributors
	tempDB.Count(&totalContributors)

	// Filter by status if filterByStatus is either 0 or 1
	if filterByStatus == 0 || filterByStatus == 1 {
		tempDB = tempDB.Where("status = ?", filterByStatus)
	}

	tempDB.Count(&resultNum)

	// Sort the contributors
	if sort != "" {
		tempDB = tempDB.Order("contributors." + sort + " " + order)
	}

	// Paginate the contributors
	if pageSize > 0 {
		tempDB = tempDB.Limit(pageSize)
		if pageNum > 0 {
			tempDB = tempDB.Offset((pageNum - 1) * pageSize)
		}
	}

	// Get the contributors
	err = tempDB.Find(&contributors).Error

	return contributors, totalContributors, resultNum, err
}



func CreateContributor(userName string, userID string, image string, link string) (contributor Contributor, err error) {
	contributor.UserID = userID
	contributor.UserName = userName
	contributor.Image = image
	contributor.Link = link
	contributor.Status = 1
	contributor.CreatedAt = time.Now()
	contributor.UpdatedAt = time.Now()

	err = DBManager.Create(&contributor).Error
	return contributor, err
}
