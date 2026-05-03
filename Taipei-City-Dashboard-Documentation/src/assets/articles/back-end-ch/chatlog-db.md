## 概述

對話紀錄用來紀錄 user 與 chatbot 之間的對話，紀錄內容以利於之後擴充支援上下文.


## chatlog

`PK` `id` `FK` `user_id`

```go
type ChatLog struct {
	ID         int       `json:"id" gorm:"column:id;autoincrement;primaryKey"`
	Session    string    `json:"session"   gorm:"column:session;type:varchar;not null`
	Question   string 	 `json:"question" gorm:"column:question;type:text"`
	Answer     string    `json:"answer" gorm:"column:answer;type:text"`
	IPAddress  string    `json:"ip_address" gorm:"column:ip_address;type:varchar(45);not null"`
	UserID     int       `json:"-" gorm:"column:user_id;type:int;not null"`
	CreatedAt  time.Time `json:"created_at" gorm:"column:created_at;type:timestamp with time zone;not null"`
	UpdatedAt  time.Time `json:"-" gorm:"column:updated_at;type:timestamp with time zone;not null"`
}
```


**值得注意的欄位：**

`session` 是字串
