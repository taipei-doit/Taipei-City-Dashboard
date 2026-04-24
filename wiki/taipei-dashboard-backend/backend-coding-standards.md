# Backend Coding Standards

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [code style](../../raw/taipei-dashboard-backend/code style.md); [Go Backend](../../raw/taipei-dashboard-backend/Go Backend.md)

## Overview

Backend contributions follow Go and project-specific conventions for formatting, naming, file layout, and responsibility placement. The backend uses `gopls` for formatting and linting, and contributions should resolve warnings and errors before pull request review.

## Formatting and Linting

The project uses `gopls`, typically installed with the VS Code Go extension. The repository includes `.vscode` settings that format code according to project guidelines on save, and the docs state those settings should not be modified.

Before opening a pull request, contributors must resolve `gopls` warnings and errors.

## Naming

Folder names should be unique, concise, one-word, and lowercase where practical because Go treats folders as packages.

File names should be concise and lowercase where possible. Multi-word file names use camel case, such as `componentConfig.go`.

Exported variables and functions use PascalCase. Package-private variables and functions use camelCase. Function names should generally start with a verb, such as `set`, `handle`, `execute`, or `show`.

## File Structure

Go files should be organized in this order:

1. Package declaration and package description.
2. Imports, grouped as standard library, internal imports, then third-party imports.
3. Global variables or structs when needed.
4. Functions.

Comments should be added where they materially improve clarity.

## Placement Rules

New request-routing or request-preparation functions belong in `/app/middlewares`. Functions that respond to the client belong in `/app/controllers`. Database interaction belongs in `/app/models`. Shared helper functions that do not fit those categories belong in `/app/utils`.

## See Also

- [Backend Architecture and Databases](backend-architecture-and-databases.md)
- [Design and Code Standards](../taipei-city-dashboard/design-and-code-standards.md)
