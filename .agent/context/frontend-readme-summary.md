# Frontend README Summary for Agents

This summary is derived from `Taipei-City-Dashboard-FE/README.md` and should be read before editing frontend code.

## Project
Taipei City Dashboard FE is a Vue-based open-source city data visualization frontend.

## Key Architecture
- `src/dashboardComponent/` is the core dashboard component library.
- `src/dashboardComponent/components/` stores all chart components.
- `src/dashboardComponent/DashboardComponent.vue` dynamically renders chart components through `returnChartComponent()`.
- `src/dashboardComponent/utilities/chartTypes.ts` maps chart keys to Chinese display names.
- `src/store/` contains Pinia stores.
- `src/router/axios.js` exports the Axios instance.

## Existing Stores
- `contentStore.js`: dashboards, components, chart data, API loading/cache.
- `mapStore.js`: Mapbox instance, layers, GeoJSON filters, camera/view state.
- `authStore.js`: auth token, login state, device/narrow viewport detection.
- `dialogStore.js`: dialog visibility.
- `adminStore.js`: admin data.
- `chatStore.js`: AI chat state.

## Existing Chart Types
Refer to `.agent/context/chart-inventory.md` before adding charts.

## ComponentConfig
Refer to `.agent/context/data-schemas.md` before creating mock data or binding API data.

## Design System
Use CSS variables from `src/assets/styles/globalStyles.css`, including:
- `--color-background`
- `--color-component-background`
- `--color-border`
- `--color-highlight`
- `--color-normal-text`
- `--color-complement-text`
- `--color-overlay`
- `--color-taipei`
- `--color-metrotaipei`

## Icons
Use Material Icons Round via span text:
```html
<span>map</span>
<span>settings</span>
```

## Responsive Classes
- `hide-if-mobile`: hidden under 1000px.
- `show-if-mobile`: visible only under 1000px.

## New Component Checklist
- Confirm whether an existing chart type can be reused.
- Props match the project chart component conventions.
- Use CSS variables instead of hardcoded colors where possible.
- Use Material Icons Round format.
- Update `chartTypes.ts`.
- Update `DashboardComponent.vue` `returnChartComponent()`.
- Add preview SVG.
