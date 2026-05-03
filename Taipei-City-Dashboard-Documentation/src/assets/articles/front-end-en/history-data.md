## History Config

To correctly render history data, several parameters need to be set and passed into the component configuration as mentioned in [this previous article](/front-end/introduction-to-components#component-configuration). The complete history config object can be found below.

```json
{
	"color": null, // Null || Array of Strings; Defaults to chart colors if null
	"range": ["halfyear_ago", "year_ago"], // Array of Strings; Time ago to query from database
	"unit": "棟" // Null || String; Data unit; Defaults to chart unit if null
}
```

[`DB` `dashboardmanager.components`](/back-end/components-db)

The `history_config` object is stored directly in the `components` table.

> **i01**
> The time terms supported for the `range` parameter are `month_ago`, `quarter_ago`, `halfyear_ago`, `year_ago`, `twoyear_ago`, `fiveyear_ago` or `tenyear_ago`.
