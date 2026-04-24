# Data-End Coding Standards

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [code style](../../raw/taipei-dashboard-dataend/code style.md); [dag code](../../raw/taipei-dashboard-dataend/dag code.md)

## Overview

The data end uses Python and generally follows PEP 8, with project-specific allowances for Airflow import placement and Black-style formatting. Developers are expected to run linting, import sorting, and formatting checks before opening pull requests.

## Tooling Expectations

The documentation uses VS Code as the reference IDE. Before opening a pull request, developers should address Pylint extension warnings as much as possible, sort imports with Isort, and format with Black Formatter.

The data-end style guide is scoped to Python data-end code. Front-end and backend style rules live in their own documentation.

## Formatting Rules

The project uses four spaces for indentation and a 100-character line length. Long calls and definitions should be wrapped inside parentheses, with the outer expression aligned and internal content indented one level. If a long condition has no existing parentheses, add parentheses instead of using backslash continuation.

Backslash line continuation should be avoided because it can cause parsing problems in some settings.

Inline comments should have one space after `#` and at least two spaces between code and the comment marker. Commas, semicolons, and colons should be followed by spaces. Keyword arguments should not use spaces around `=`.

## Naming Rules

Variable, function, and file names should be meaningful. Directories, files, ordinary variables, and functions use snake case. Classes use UpperCamelCase. Module-level constants use uppercase words separated by underscores.

## Airflow-Specific Python Notes

The DAG authoring guide shows imports inside the ETL function in its example but also notes Airflow's top-level-code concerns. The practical rule is to keep DAG files simple and avoid expensive top-level work, because Airflow parses DAG files frequently. ETL logic should be wrapped in a function and passed to `CommonDag.create_dag`.

## See Also

- [Airflow DAG Development](airflow-dag-development.md)
- [Design and Code Standards](../taipei-city-dashboard/design-and-code-standards.md)
- [Backend Coding Standards](../taipei-dashboard-backend/backend-coding-standards.md)
