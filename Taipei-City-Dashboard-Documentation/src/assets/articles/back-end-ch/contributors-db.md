## contributors

`PK` `id`

```go
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
```

**值得注意的欄位：**

`user_id` 指的是應該用來填入組件設定中的 contributors 欄位的貢獻者 id。除非有重複，建議使用貢獻者的名稱。

`image` 應該是貢獻者 GitHub 帳號大頭貼的 URL。

`include` 是一個布林欄位，如果貢獻者應該包含在平台上的貢獻者列表中，則應將其填為 `true`。如果填為 `false`，則不會將貢獻者包含在列表中。
