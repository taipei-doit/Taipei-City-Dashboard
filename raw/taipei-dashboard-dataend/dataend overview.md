---
title: "Taipei City Dashboard"
source: "https://test-citydashboard.taipei/documentation/data-end/dataend"
author:
published:
created: 2026-04-24
description: "The documentation website of Taipei City Dashboard, Taipei Urban Intelligence Center, Department of Information Technology, Taipei City Government"
tags:
  - "clippings"
---
## Data End Overview

資料端的任務是為臺北城市儀表板收集並初步標準化資料。我們會盡可能地收集資料，並將篩選適當資料的步驟交由後端執行，使前端得以高效渲染。

本專案著重在降低開發門檻，讓需要撰寫的 Python 程式碼簡單明瞭，並且隱藏 Airflow 的互動細節，即使不了解 Airflow 也能進行開發。

我們希望讓任何曾用 Python 處理過開放資料的人，經過稍微改動後，都能進行貢獻。讓程式出得去，貢獻進得來，成為資料處理大平台。

> #### Warning - 1
> 
> 本專案所稱"資料"，特指資料端收集與處理，供臺北城市儀表板呈現的應用資料。不包含各端所需的管理、驗證、權限等資料。

> #### Information - 1
> 
> 臺北城市儀錶板的資料端與後端的接觸點僅在資料庫，無其他耦合。

## 資料流流程

資料端採傳統的 ETL 流程： 抽取（Extract） -> 轉換（Transform） -> 儲存（Load）。最終資料儲存於 PostgreSQL 資料庫。

> #### Information - 2
> 
> 後續將以 PSQL 簡稱 PostgreSQL 資料庫。

> #### Warning - 2
> 
> 後續將用 `/folder/folder/file` 的方式表示檔案路徑，用 `db:server/database/table` 表示資料庫中的路徑。

[auto\_fix\_highEdit this Page on Github](https://github.com/taipei-doit/Taipei-City-Dashboard-Documentation/edit/main/src/assets/articles/data-end-en/dataend.md)