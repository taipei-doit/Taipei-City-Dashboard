package models

import (
	"time"
)


type ChatLog struct {
	ID             int    			`json:"id"        		gorm:"column:id;autoincrement;primaryKey"`
	Session	   	   string 			`json:"session".        gorm:"column:session;type:varchar;not null;index:idx_chat_logs_session"`
	Question	   string 			`json:"question"        gorm:"column:question;type:text"`
	Answer         string 			`json:"answer"          gorm:"column:answer;type:text"`
	UserID         int 				`json:"-" 				gorm:"column:user_id;type:int;not null;index:idx_chat_logs_user_id"`
	CreatedAt      time.Time        `json:"created_at" 		gorm:"column:created_at;type:timestamp with time zone;not null"`
	UpdatedAt      time.Time        `json:"-" 				gorm:"column:updated_at;type:timestamp with time zone;not null"`
}


func CreateChatLog(Session string, Question string, Answer string,UserID int)(chatLog ChatLog,err error){

	chatLog = ChatLog{
		Session:   Session,
		Question:  Question,
		Answer:    Answer,
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