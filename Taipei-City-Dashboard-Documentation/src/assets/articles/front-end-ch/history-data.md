## 歷史軸配置

為了正確地呈現歷史軸，需要將歷史軸配置填入組件配置中的`history_config`參數，詳細內容請參閱[這篇先前的文章](/front-end/introduction-to-components#component-configuration)。完整的圖表配置(Object)如下所示。

```json
{
	"color": null, // Null || Array of Strings; 如為 null 則使用圖表顏色
	"range": ["halfyear_ago", "year_ago"], // Array of Strings; 從資料庫查詢的時間範圍
	"unit": "棟" // Null || String; 資料的單位; 如為 null 則使用圖表單位
}
```

[`DB` `dashboardmanager.components`](/back-end/components-db)

`history_config`物件直接儲存在`components` table 中。

> **i01**
> `range` 參數支援的時間區間為 `month_ago`、`quarter_ago`、`halfyear_ago`、`year_ago`、`twoyear_ago`、`fiveyear_ago` 或 `tenyear_ago`.
