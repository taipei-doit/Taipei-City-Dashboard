# UI Customization and Dialogs

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [客製化樣式](../../raw/客製化樣式.md); [客製化彈跳視窗](../../raw/客製化彈跳視窗.md); [設計指南](../../raw/設計指南.md)

## Overview

Taipei City Dashboard uses plain CSS and SCSS rather than a UI library, with global variables for shared colors, fonts, and viewport units. Dialogs are Vue components controlled by `dialogStore`; newer dialog implementations should use `DialogContainer` to centralize teleport, transition, conditional rendering, and overlay behavior.

## Styling Scope

Most project styling is implemented in CSS or SCSS, except elements rendered by third-party libraries such as Mapbox and ApexCharts. Global CSS styles live in `/src/assets/styles`; scoped component styles live at the bottom of Vue files and use SCSS.

The project defines CSS variables in `globalStyles.css`, including:

- `--color-background`: `#090909`
- `--color-border`: `#494b4e`
- `--color-highlight`: `#5a9cf8`
- `--color-normal-text`: `white`
- `--color-complement-text`: `#888787`
- `--color-component-background`: `#282a2c`
- `--color-overlay`: dialog overlay color
- font scale variables from `--font-xl` through `--font-s`
- `--font-icon`: Material Icons Round

Material Icons are loaded through Google Fonts in `index.html`.

## Dialog State

Every dialog is a Vue component whose visibility is controlled by `dialogStore.dialogs`. Dialog names use the camelCase form of their Vue component filename.

The documented dialog state includes admin dialogs such as `adminComponentSettings`, `adminAddEditDashboards`, `adminEditIssue`, `adminAddComponent`, `adminDeleteDashboard`, `adminEditUser`, `adminAddEditContributor`, and `adminDeleteContributor`; and public dialogs such as `addComponent`, `addDashboard`, `dashboardSettings`, `initialWarning`, `login`, `mobileLayers`, `mobileNavigation`, `moreInfo`, `notificationBar`, `reportIssue`, `userSettings`, `embedComponent`, `contributorsList`, `contributorInfo`, `addPin`, `addViewPoint`, and `findClosestPoint`.

## Dialog Implementation

The older explicit pattern wraps a conditionally rendered dialog in Vue `Teleport` and `Transition`, with overlay and dialog container elements. The newer recommended pattern uses `DialogContainer`:

```html
<DialogContainer dialog="initialWarning" @on-close="handleClose">
    <div class="initialwarning">
        <!-- dialog content -->
    </div>
</DialogContainer>
```

Opening a normal dialog calls `dialogStore.showDialog(dialogName)`. Closing dialogs calls `dialogStore.hideAllDialogs`, which hides all dialogs except `notificationBar`.

Three dialogs need special state:

- `moreInfo` opens through `dialogStore.showMoreInfo(componentConfig)`.
- `reportIssue` opens through `dialogStore.showReportIssue(name, id)`.
- `notificationBar` opens through `dialogStore.showNotification(status, message)`, where status can be `success` or `fail`.

When adding a dialog, create the Vue component, register its state in `dialogStore`, and add the component near the UI element that triggers it. The documentation warns against adding the same dialog component in multiple places because it can render duplicates.

## Design Fit

The UI direction emphasizes simple data visualization, concise surface text, important controls in blue, and detailed component information inside popups rather than directly on dashboards. Component surfaces should expose title, source, update frequency, and tags; deeper descriptions, use cases, source links, and contributor data belong in the more-information dialog.

## See Also

- [Design and Code Standards](design-and-code-standards.md)
- [Map Features and Configuration](map-features-and-configuration.md)
- [Authentication, Admin, and Dashboard Operations](auth-admin-and-dashboard-operations.md)
