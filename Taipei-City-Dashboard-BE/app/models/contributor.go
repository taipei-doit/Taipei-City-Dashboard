package models

import (
	"time"
)

/* ----- Models ----- */

type Contributor struct {
	ID          int64     `json:"id" gorm:"column:id;autoincrement;primaryKey"`
	UserID      string    `json:"user_id" gorm:"column:user_id;type:varchar;not null"`
	UserName    string    `json:"user_name" gorm:"column:user_name;type:varchar;not null"`
	Image       string    `json:"image" gorm:"column:image;type:text"`
	Link        string    `json:"link" gorm:"column:link;type:text;not null"`
	Identity    *string   `json:"identity" gorm:"column:identity;type:varchar"`
	Description *string   `json:"description" gorm:"column:description;type:text"`
	Include     *bool     `json:"include" gorm:"column:include;type:boolean;default:false;not null"`
	CreatedAt   time.Time `json:"created_at" gorm:"column:created_at;type:timestamp with time zone;not null"`
	UpdatedAt   time.Time `json:"updated_at" gorm:"column:updated_at;type:timestamp with time zone;not null"`
}

/* ----- Handlers ----- */

func GetAllContributors(pageSize int, pageNum int, sort string, order string) (contributors []Contributor, totalContributors int64, err error) {
	tempDB := DBManager.Table("contributors")

	// Count the total amount of contributors
	tempDB.Count(&totalContributors)

	// Sort the contributors
	if sort != "" {
		tempDB = tempDB.Order("contributors." + sort + " " + order)
	} else {
		tempDB = tempDB.Order("contributors.id asc")
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

	return contributors, totalContributors, err
}

func GetContributorByID(ID int) (contributor Contributor, err error) {
	err = DBManager.Table("contributors").Where("id = ?", ID).First(&contributor).Error
	return contributor, err
}

func CreateContributor(userID string, userName string, image string, link string, identity *string, description *string, include *bool) (contributor Contributor, err error) {
	contributor.UserID = userID
	contributor.UserName = userName
	contributor.Image = image
	contributor.Link = link
	contributor.CreatedAt = time.Now()
	contributor.UpdatedAt = time.Now()
	contributor.Identity = identity
	contributor.Description = description
	contributor.Include = include
	err = DBManager.Create(&contributor).Error
	return contributor, err
}

func UpdateContributor(ID int, userID string, userName string, image string, link string, identity *string, description *string, include *bool) (contributor Contributor, err error) {
	err = DBManager.Model(&Contributor{}).Where("id = ?", ID).Updates(map[string]interface{}{
		"user_id": userID, "user_name": userName, "image": image, "link": link, "updated_at": time.Now(),
		"identity": identity, "description": description, "include": include,
	}).Error
	if err != nil {
		return contributor, err
	}

	err = DBManager.Table("contributors").Where("id = ?", ID).First(&contributor).Error
	if err != nil {
		return contributor, err
	}

	return contributor, err
}

func DeleteContributorByID(ID int) (contributorStatus bool, err error) {
	err = DBManager.Model(&Contributor{}).Where("id = ?", ID).Delete(&Contributor{}).Error
	if err != nil {
		return false, err
	}

	return true, err
}
