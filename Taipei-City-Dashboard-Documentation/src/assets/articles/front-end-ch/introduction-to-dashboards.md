## 概覽

儀表板是相關或互補的組件集合。除了一般的儀表板外，另有兩種特殊類型，以更好地顯示特殊的組件類別。

### 圖資資訊圖層

圖資資訊圖層儀表板是一個特殊的儀表板，僅儲存包含空間資料的組件。

### 收藏

收藏儀表板與一般儀表板十分類似，唯一的區別在於組件的添加方式。用戶可以點擊任何組件右上角的愛心圖標，將組件快速添加到收藏儀表板中。收藏儀表板在用戶初次登入時會自動建立，並且無法刪除。

## 儀表板配置

無論類型為何，所有儀表板配置都以相同的格式 (Object) 儲存在單個 Array 中。下面是儀表板配置完整的參數列表。

[`GET` `/api/v1/dashboard`](/back-end/dashboard-apis) [`DB` `dashboardmanager.dashboards`](/back-end/dashboards-db)

<!-- _[使用 API 測試器測試這支 API](/api)_ -->

```json
{
    "name": "民情熱議", // String; 儀表板的名稱
    "index": "public-opinion", // String; 需為英文與獨特
    "components": [4, 5, 72], // Array; 組件的 ID
    "icon": "mic" // String; 圖標名稱（支援所有 Google Icons 圖標）
},
```
