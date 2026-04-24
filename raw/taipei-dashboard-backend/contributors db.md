---
title: "Taipei City Dashboard"
source: "https://test-citydashboard.taipei/documentation/back-end/contributors-db"
author:
published:
created: 2026-04-24
description: "The documentation website of Taipei City Dashboard, Taipei Urban Intelligence Center, Department of Information Technology, Taipei City Government"
tags:
  - "clippings"
---
## Contributors DB

## contributors

`PK` `id`

```
type Contributor struct {
    ID          int64     \`json:"id" gorm:"column:id;autoincrement;primaryKey"\`
    UserID      string    \`json:"user_id" gorm:"column:user_id;type:varchar;not null"\`
    UserName    string    \`json:"user_name" gorm:"column:user_name;type:varchar;not null"\`
    Image       string    \`json:"image" gorm:"column:image;type:text"\`
    Link        string    \`json:"link" gorm:"column:link;type:text;not null"\`
    Identity    *string   \`json:"identity" gorm:"column:identity;type:varchar"\`
    Description *string   \`json:"description" gorm:"column:description;type:text"\`
    Include     *bool     \`json:"include" gorm:"column:include;type:boolean;default:false;not null"\`
    CreatedAt   time.Time \`json:"created_at" gorm:"column:created_at;type:timestamp with time zone;not null"\`
    UpdatedAt   time.Time \`json:"updated_at" gorm:"column:updated_at;type:timestamp with time zone;not null"\`
}
```

**Columns of Note:**

`user_id` refers to the id of the contributor that should be used to fill in the contributors column in the component config. Unless there are duplicates, it is recommended to use the contributor's name.

`image` should be the URL of the contributor's GitHub profile photo.

`include` is a boolean field that should be set to `true` if the contributor should be included in the contributors list on the platform. If set to `false`, the contributor will not be included in the list.

[auto\_fix\_highEdit this Page on Github](https://github.com/taipei-doit/Taipei-City-Dashboard-Documentation/edit/main/src/assets/articles/back-end-en/contributors-db.md)