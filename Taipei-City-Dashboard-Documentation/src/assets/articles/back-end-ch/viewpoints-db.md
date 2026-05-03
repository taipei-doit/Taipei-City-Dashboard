## viewpoints

`PK` `id` `FK` `user_id`

```go
type ViewPoints struct {
	ID        int      `json:"id" gorm:"column:id;autoincrement;primaryKey"`
	UserID    int      `json:"user_id" gorm:"column:user_id;not null"`
	CenterX   float32  `json:"center_x" gorm:"column:center_x"`
	CenterY   float32  `json:"center_y" gorm:"column:center_y"`
	Zoom      float32  `json:"zoom" gorm:"column:zoom"`
	Pitch     float32  `json:"pitch" gorm:"column:pitch"`
	Bearing   float32  `json:"bearing" gorm:"column:bearing"`
	Name      string   `json:"name" gorm:"column:name"`
	PointType string   `json:"point_type" gorm:"column:point_type"`
	AuthUser  AuthUser `gorm:"foreignKey:UserID"`
}
```


**值得注意的欄位：**

`center_x` 和 `center_y` 分別是觀點的緯度和經度。

`point_type` 是觀點的類型。它可以是 `view` (地圖視角) 或 `pin` (地圖圖標)。
