# Data and Visualization Formats

> Sources: Taipei Urban Intelligence Center, 2026-04-24
> Raw: [圖表資料樣式](../../raw/圖表資料樣式.md); [支援圖表類型](../../raw/支援圖表類型.md); [歷史資料樣式](../../raw/歷史資料樣式.md); [客製化圖表](../../raw/客製化圖表.md); [資料來源與清理](../../raw/資料來源與清理.md)

## Overview

Taipei City Dashboard supports five chart data shapes: `two_d`, `three_d`, `time`, `percent`, and `map_legend`. These query types map to specific Vue chart components and are controlled through `chart_config` in component configuration. Historical views use `history_config`, while source data should prefer official Taipei open data and normalize time, spatial, and administrative district fields before ingestion.

## Data Source Principles

Project data should generally come from `data.taipei`, with central-government or public private-sector data used only when needed. The documented acquisition principle is to prefer the nearest authoritative owning agency. For Taipei-specific data, Taipei's open data platform should be preferred over central platforms when both provide similar datasets.

Data cleaning should verify consistent units, missing values, correct types, and unique identifiers. Time fields should include timezone and follow `YYYY-MM-DDThh:mm:ssTZD`, such as `2023-06-16T18:20:00+08:00`. Spatial coordinates must use WGS84/EPSG:4326. Administrative district data should handle uncommon characters and duplicate village names by pairing village-level data with district names.

## Chart Configuration

`chart_config` is stored separately in `dashboardmanager.component_charts` and joined with `components` when APIs are called. It includes:

- `color`: at least one hex color.
- `types`: one to three English chart component names.
- `unit`: display unit or `null`.
- `categories`: filled automatically when APIs are called.

Chart components live under `/src/dashboardComponents/components`. ApexCharts-based components define `chartOptions`, and some include parsing functions so that one dataset can support multiple visualizations.

## Supported Query Types

`two_d` is simple key-value data where `x` is a string and `y` is a number. It supports visualizations such as donut, bar, column, treemap, district, metro, radar, and polar area charts. District charts require the documented order of Taipei and New Taipei administrative districts.

`three_d` is key-subcategory-value data. `categories` holds the x-axis keys, and each series has a `name` plus a `data` array ordered to match `categories`. It supports column, percent bar, radar, district, heatmap, polar area, indicator, and text-unit charts.

`time` is timestamp key-value data. Additional series are allowed, but their timestamps must align with the first series. It supports comparison timelines, stacked timelines, and column-line charts.

`percent` data provides numerator and remainder series; the chart component computes the percentage. It supports gauge, percent bar, goal bar, and icon-percent charts.

`map_legend` stores legend items as configuration objects with `name`, `type`, optional `icon`, and optional `value`. It supports `MapLegend`.

## Chart Types

The documented chart set includes `BarChart`, `BarPercentChart`, `ColumnChart`, `DonutChart`, `GuageChart`, `RadarChart`, `TimelineSeparateChart`, `TimelineStackedChart`, `TreemapChart`, `DistrictChart`, `MetroChart`, `HeatmapChart`, `PolarAreaChart`, `ColumnLineChart`, `BarChartWithGoal`, `IconPercentChart`, `IndicatorChart`, and `TextUnitChart`.

Special formats exist for several chart types. `MetroChart` uses station-direction keys and compact car-crowding values. `IndicatorChart` uses 3D data where category ranges determine the active bucket. `TextUnitChart` uses the `icon` field to display unit or supplemental text.

## Custom Chart Components

When a page loads, the app fetches component statistical data, adds it to the chart configuration as `chart_data`, and stores it in `contentStore`.

Dashboard and map pages render charts through `ComponentContainer` and `ComponentMapContainer` under `/src/components/components`. If a component has multiple chart types, the container shows gray buttons labeled by chart name, and the selected chart name controls conditional rendering.

Chart Vue components receive `chart_config`, `activeChart`, `series`, `map_config`, and, for filter-capable charts, `map_filter`. ApexCharts-based charts define `chartOptions` and may define parsing computed properties so the same data can be reused across chart types. Custom non-ApexCharts components can implement their own template and click handlers while still following the same prop-driven structure.

To add a new chart type, create the Vue chart component, define ApexCharts options if needed, add the chart name to `/src/assets/configs/apexcharts/chartTypes.js`, globally register the component in `/src/main.js`, then reference the chart name from a component configuration.

## Historical Data

Historical timelines use `history_config` stored directly on `dashboardmanager.components`. Its fields are `color`, `range`, and `unit`. If `color` or `unit` is `null`, chart color or chart unit is reused. Supported ranges are `month_ago`, `quarter_ago`, `halfyear_ago`, `year_ago`, `twoyear_ago`, `fiveyear_ago`, and `tenyear_ago`.

## See Also

- [Hackathon Rules and Delivery Requirements](hackathon-rules-and-delivery-requirements.md)
- [Platform Model](platform-model.md)
- [Map Features and Configuration](map-features-and-configuration.md)
- [Design and Code Standards](design-and-code-standards.md)
