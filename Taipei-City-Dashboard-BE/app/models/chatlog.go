package models

import (
	"context" // Add context import
	"time"
)


type ChatLog struct {
	ID             int    			`json:"id"        		gorm:"column:id;autoincrement;primaryKey"`
	Session	   	   string 			`json:"session".        gorm:"column:session;type:varchar;not null;index:idx_chat_logs_session"`
	Question	   string 			`json:"question"        gorm:"column:question;type:text"`
	Answer         string 			`json:"answer"          gorm:"column:answer;type:text"`
	IPAddress      string           `json:"ip_address"      gorm:"column:ip_address;type:varchar(45);not null"`
	UserID         int 				`json:"-" 				gorm:"column:user_id;type:int;not null;index:idx_chat_logs_user_id"`
	CreatedAt      time.Time        `json:"created_at" 		gorm:"column:created_at;type:timestamp with time zone;not null"`
	UpdatedAt      time.Time        `json:"-" 				gorm:"column:updated_at;type:timestamp with time zone;not null"`
}


func CreateChatLog(Session string, Question string, Answer string, IPAddress string, UserID int)(chatLog ChatLog,err error){

	chatLog = ChatLog{
		Session:   Session,
		Question:  Question,
		Answer:    Answer,
		IPAddress: IPAddress,
		UserID:    UserID,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err = DBManager.Create(&chatLog).Error
	if err != nil {
		return chatLog, err
	}

	return chatLog, nil
}

func GetALLChatLogSession(UserID int)(chatLogList []ChatLog,err error){

	err = DBManager.Raw(`
		SELECT DISTINCT ON (session) *
		FROM chat_logs
		WHERE user_id = ?
		ORDER BY session, created_at ASC
	`, UserID).Scan(&chatLogList).Error
	
	if err != nil {
		return chatLogList, err
	}

	return chatLogList, nil
}

// DeleteOldChatLogs deletes chat logs older than the specified number of months.
// It returns the number of rows affected and an error, if any.
func DeleteOldChatLogs(ctx context.Context, months int) (int64, error) { // Modified function signature
    cutoffDate := time.Now().AddDate(0, -months, 0)
    db := DBManager.WithContext(ctx).Where("created_at < ?", cutoffDate).Delete(&ChatLog{}) // Use WithContext
    return db.RowsAffected, db.Error // Return rows affected and error
}

func GetChatLogDetailBySession(Session string,UserID int)(chatLogList []ChatLog,err error){

	err = DBManager.
		Table("chat_logs").
		Where("user_id = ?", UserID).
		Where("session = ?", Session).
		Find(&chatLogList).
		Error

	if err != nil {
		return chatLogList, err
	}

	return chatLogList, nil
}