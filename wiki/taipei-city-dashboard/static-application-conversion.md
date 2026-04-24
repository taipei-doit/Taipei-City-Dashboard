# Static Application Conversion

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [轉為純靜態網頁](../../raw/轉為純靜態網頁.md); [檔案儲存系統](../../raw/檔案儲存系統.md); [用戶驗證](../../raw/用戶驗證.md); [編輯儀表板](../../raw/編輯儀表板.md)

## Overview

Taipei City Dashboard can be converted into a fully static application when the target data is static. The conversion removes authentication, admin pages, user-specific mutation flows, and backend API dependencies, then replaces GET requests with static files under `/public`.

## When Static Conversion Fits

The documentation frames static conversion as suitable when the application only needs to present static statistical and spatial data. In that mode, the project keeps its visualization and map capabilities but drops dynamic web-application features that require a backend.

## Route and Page Changes

Router restrictions related to authentication should be removed. Admin pages should be removed. Sidebars for component and component-information pages should also be removed when they depend on dynamic app behavior.

## Backend-Dependent Features to Remove

Features that require backend state should be removed, including dashboard modification, issue reporting, and user settings. The associated components, dialogs, and functions should be deleted from the static application. A practical test is whether the feature only works after login; if so, it likely depends on the backend.

## API Replacement

The `/public` directory contains sample components, dashboards, charts, history, and map data. Static conversion should replace backend `GET` calls with file reads from these static assets. All non-GET API calls should be removed.

## Repository Setup

The front-end folder `/Taipei-City-Dashboard-FE` should be moved to a new repository, and a `.env` file containing front-end variables should be added at the root. After API removal and static data replacement, the app can be deployed to any static web hosting service.

## See Also

- [Platform Model](platform-model.md)
- [Authentication, Admin, and Dashboard Operations](auth-admin-and-dashboard-operations.md)
- [Data and Visualization Formats](data-and-visualization-formats.md)
