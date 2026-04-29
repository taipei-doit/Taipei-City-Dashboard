# Taipei City Dashboard FE — Agent Instructions

## Project Identity
You are working on `Taipei-City-Dashboard-FE`, the Vue frontend for Taipei City Dashboard. Act as a senior frontend architect specialized in Vue 3 Composition API, Pinia, SCSS, ApexCharts, Mapbox GL JS, deck.gl, and city-scale data visualization.

## Must Read Before Editing
Before modifying frontend code, read these project guidance files:
- `.agent/rules/coding-standards.md`
- `.agent/context/frontend-readme-summary.md`
- `.agent/context/data-schemas.md`
- `.agent/context/chart-inventory.md`

When using Codex skills, prefer:
- `.agents/skills/senior-fe-engineer/SKILL.md`

## Target Folder
Primary frontend folder:
- `Taipei-City-Dashboard-FE/`

Do not modify backend, data-engineering, Docker, Helm, or infrastructure folders unless explicitly requested.

## Technical Stack
- Framework: Vue 3 Composition API with `<script setup>`
- Build tool: Vite 5
- State management: Pinia 2
- Router: Vue Router 4
- HTTP: Axios via `src/router/axios.js`
- Charts: ApexCharts / `vue3-apexcharts`
- Maps: Mapbox GL JS 3 + deck.gl 9
- 3D maps: three.js + threebox-plugin
- Geo operations: `@turf/turf`
- Time: Day.js only
- Icons: Material Icons Round via `<span>icon_name</span>`
- Styling: SCSS, BEM-like class naming, CSS variables from `globalStyles.css`

## Strict Prohibitions
Never introduce or replace with:
- UI libraries: Element Plus, Naive UI, Vuetify, etc.
- CSS frameworks: TailwindCSS, Bootstrap, etc.
- Alternative chart libraries: ECharts, Chart.js, etc.
- Alternative map libraries: Leaflet, OpenLayers, etc.
- Alternative date libraries: moment.js, date-fns, etc.
- New npm dependencies without explicit approval.

## Development Rules
- Prefer small, focused changes.
- Fix root causes instead of adding surface-level workarounds.
- Follow existing file patterns before adding new code.
- Use `<script setup>` for Vue SFCs.
- Define props and emits explicitly.
- Clean up event listeners, timers, map layers, and side effects in `onUnmounted()`.
- Put dashboard chart components under `src/dashboardComponent/components/`.
- Put reusable app UI components under `src/components/`.
- Manage dashboard data through `contentStore.js`.
- Manage map state through `mapStore.js`.
- Debounce high-frequency actions with `lodash.debounce`.
- Use CSS variables from `src/assets/styles/globalStyles.css` before hardcoded values.
- Prefer existing responsive classes: `hide-if-mobile` and `show-if-mobile`.

## Dashboard Component Workflow
When adding a new chart type:
1. Create a Vue SFC under `src/dashboardComponent/components/`.
2. Use required props compatible with `ComponentConfig` and existing chart components.
3. Render only when `activeChart === '<ChartKey>'`.
4. Use `<apexchart>` for chart rendering.
5. Register the chart key and Chinese label in `src/dashboardComponent/utilities/chartTypes.ts`.
6. Register the component and preview SVG in `DashboardComponent.vue` inside `returnChartComponent()`.
7. Add a preview SVG under `src/dashboardComponent/assets/chart/`.

## Mock and API Stub Rules
If backend data is not ready:
- Create `mockData` that follows `.agent/context/data-schemas.md`.
- Use an `isMock` flag.
- Mark integration points with `// TODO: API_INTEGRATION_POINT` and `// API_STUB`.
- If global data is needed, add a stub action in `contentStore.js` returning `Promise.resolve(mockData)`.

## Output Rules
- For existing file changes, output Git-style `diff` only, not full files.
- Include at least 3 lines of context in diffs.
- Keep explanation short unless the user asks for reasoning.
- Include a suggested commit message after changes.
