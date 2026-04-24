---
title: "Taipei City Dashboard"
source: "https://test-citydashboard.taipei/documentation/back-end/code-style"
author:
published:
created: 2026-04-24
description: "The documentation website of Taipei City Dashboard, Taipei Urban Intelligence Center, Department of Information Technology, Taipei City Government"
tags:
  - "clippings"
---
## Code Style

> #### Warning - 1
> 
> This article only covers the coding style for the back-end. If you will also be developing our front-end, please refer to [the front-end coding style guide](https://test-citydashboard.taipei/documentation/front-end/code-style).

## Code Linting

This project uses `gopls` for formatting and linting code. This tool is automatically included when you install the go extension for VSCode. In the root repository, there is a folder called `.vscode` which contains settings for VS Code that will enable you to format your code in accordance with our guidelines whenever you save your document. Any modifications to the settings are not allowed.

Before opening a pull request, you must ensure that all warnings and errors shown by gopls are resolved. The process of opening a pull request will be explained in greater detail [here](https://test-citydashboard.taipei/documentation/back-end/open-a-pull-request).

## Variable and File Naming

As a general rule of thumb, all new variable and file names should be unique and descriptive. If your contribution contains variable or file names deemed unclear, you will be asked to modify them. Some more specified guidelines are listed below.

### Folders

As Go regards folders as packages, all new folder names should be unique and concise, preferably one word in lowercase (e.g `db`).

### Files

All new file names should be concise, preferably one word in lowercase. If a file contains multiple words, they should in Camel case (e.g. `componentConfig.go`).

### Variables and Functions

Per Go's specifications, variables and functions that are exported should be in Pascal case (e.g. `GetAllComponents`, first letter capitalized), while variables and functions only used within a package should be in Camel case (e.g. `createTempComponentDB`). In addition, we highly recommend that function names start with a verb such as set, handle, execute, show, etc.

## Document Structure

As a general rule of thumb, all documents should be formatted in a clear and logical order. Comments should be added if necessary to increase clarity. If your contribution contains documents not formatted to this project’s standards, you will be asked to modify them. Some more specified guidelines are listed below.

```
// Package postgres... (1. Package declaration + package description)
package postgres

// (2. Imports)
import (
    // (2.1 Standard library imports)
    "crypto/sha256"
    "fmt"
    "os"
    "time"

    // (2.2 Internal imports)
    "TaipeiCityDashboardBE/internal/db/postgres/models"
    "TaipeiCityDashboardBE/logs"

    // (2.3 Third-party imports)
    "gorm.io/driver/postgres"
    "gorm.io/gorm"
)

// (3. Global variables or structs if applicable)
var (
    DBDashboard *gorm.DB
    DBManager   *gorm.DB
)

// (4. Functions)
func ConnectToDatabases(dbNames ...interface{}) {
    // ...
}
```

[auto\_fix\_highEdit this Page on Github](https://github.com/taipei-doit/Taipei-City-Dashboard-Documentation/edit/main/src/assets/articles/back-end-en/code-style.md)