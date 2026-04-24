---
title: "Taipei City Dashboard"
source: "https://test-citydashboard.taipei/documentation/back-end/issues-db"
author:
published:
created: 2026-04-24
description: "The documentation website of Taipei City Dashboard, Taipei Urban Intelligence Center, Department of Information Technology, Taipei City Government"
tags:
  - "clippings"
---
## Issues DB

## issues

`PK` `id`

```
type Issue struct {
    ID           int64     \`json:"id"            gorm:"column:id;autoincrement;primaryKey"\`
    Title        string    \`json:"title"         gorm:"column:title;type:varchar;not null"\`
    UserName     string    \`json:"user_name"     gorm:"column:user_name;type:varchar;not null"\`
    UserID       string    \`json:"user_id"       gorm:"column:user_id;type:varchar;not null"\`
    Context      string    \`json:"context"       gorm:"column:context;type:text"\`
    Description  string    \`json:"description"   gorm:"column:description;type:text;not null"\`
    DecisionDesc string    \`json:"decision_desc" gorm:"column:decision_desc;type:text"\`
    Status       string    \`json:"status"        gorm:"column:status;type:varchar;not null"\`
    UpdatedBy    string    \`json:"updated_by"    gorm:"column:updated_by;type:varchar;not null"\`
    CreatedAt    time.Time \`json:"created_at"    gorm:"column:created_at;type:timestamp with time zone;not null"\`
    UpdatedAt    time.Time \`json:"updated_at"    gorm:"column:updated_at;type:timestamp with time zone;not null"\`
}
```

**Columns of Note:**

`status` is either `待處理` (pending), `處理中` (ongoing), `已處理` (completed), or `不處理` (rejected); `decision_desc` must be filled out if `status` is `已處理` or `不處理`.

[auto\_fix\_highEdit this Page on Github](https://github.com/taipei-doit/Taipei-City-Dashboard-Documentation/edit/main/src/assets/articles/back-end-en/issues-db.md)