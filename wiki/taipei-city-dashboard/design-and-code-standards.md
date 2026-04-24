# Design and Code Standards

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [設計指南](../../raw/taipei-dashboard-frontend/設計指南.md); [程式撰寫規範](../../raw/taipei-dashboard-frontend/程式撰寫規範.md); [客製化樣式](../../raw/taipei-dashboard-frontend/客製化樣式.md); [資料來源與清理](../../raw/taipei-dashboard-frontend/資料來源與清理.md)

## Overview

Contributions to Taipei City Dashboard should preserve a minimal, consistent, data-first interface and follow established Vue, CSS, linting, and data-cleaning conventions. The design rules focus on readable visualization and controlled information density, while code rules focus on predictable naming, file order, linting, and style organization.

## UI and UX Principles

The platform's design goal is to help users browse, explore, and cross-compare Taipei and New Taipei data. Contribution guidance emphasizes:

- Simplicity: show the most representative chart types and move detailed information into dialogs.
- User experience: use clear, descriptive component names that encode source, interval, and statistical method when relevant.
- Appropriate information density: surface essentials on component cards and move full details into the more-information dialog.
- Compatibility: define shared formats, such as administrative district order, so datasets remain comparable.
- Consistency: keep chart and map color behavior aligned, and name related components so their relationship is obvious.

## Visual System

The visual system uses dark backgrounds, white or gray text, blue highlights, and restrained chart/map colors. Important variables include background `#090909`, border `#494b4e`, highlight `#5a9cf8`, complement text `#888787`, and component background `#282a2c`.

Chart and map colors should prefer medium or low saturation. Similar hues should express similar categories; gradients should express increasing or decreasing values; unrelated categories can use clearly distinct colors.

Text levels are defined through CSS variables: project title text uses `--font-l`, most headings use `--font-m`, and body or note text uses `--font-s`. Spacing for large elements should usually reuse the same variable scale.

## Linting and Formatting

The project uses Prettier for formatting and ESLint for code checks. Contributors should not change `.eslintrc.json` or `.prettierrc`. Before opening a pull request, contributors must run `npm run lint` from the project root and fix issues.

VS Code with Prettier and ESLint extensions is recommended. The repository includes `.vscode` settings to format on save.

## Naming Rules

Vue component names must contain at least two English words and use PascalCase, such as `MapView`.

Functions should generally start with verbs and use camelCase, such as `hideAllDialogs`.

Variables should be descriptive and use camelCase. The documentation explicitly disallows `var` unless absolutely necessary.

CSS class names should use kebab-case. Each Vue component root class should match the filename lowercased without spaces, and nested class names should prefix from that root class.

## File and Style Order

Vue files should follow a predictable order: imports, store declarations, props and emits, local data, computed properties, methods, lifecycle hooks, template, then scoped SCSS.

CSS properties should be ordered by category: dimensions, display, position, margin/padding, border, background, font, animation, transition, then other properties. Selectors such as `:hover` should come after the class's main styles.

## Data Hygiene

Code contributions that introduce data should also follow data-cleaning expectations. Prefer official data sources, normalize units and types, include unique IDs when source data lacks them, use timezone-aware timestamps, convert coordinates to WGS84/EPSG:4326, and disambiguate duplicate local administrative names.

## See Also

- [UI Customization and Dialogs](ui-customization-and-dialogs.md)
- [Data and Visualization Formats](data-and-visualization-formats.md)
- [Platform Model](platform-model.md)
- [Backend Coding Standards](../taipei-dashboard-backend/backend-coding-standards.md)
