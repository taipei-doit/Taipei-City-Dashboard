# Data Schemas (TypeScript Definitions)

## ComponentConfig
這是儀表板組件的核心設定結構，所有 Mock 資料必須符合此格式：

```typescript
type ComponentConfig = {
  id: number;              // ID
  index: string;           // 識別字串（英文）
  name: string;            // 顯示名稱（中文）
  source: string;          // 資料來源
  time_from: string;       // "static" | "current" | "1month" 等
  time_to: string;         // "now" 或日期
  chart_config: {
    color: string[];       // Hex 顏色陣列
    types: string[];       // ["BarChart", "LineChart"] 等
    unit: string | null;   // 單位
    categories: string[] | null; // X 軸標籤
  };
  chart_data: any;         // 實際存放資料處
  map_config: any[] | null;
};

type MapConfig = {
  index: string;           // 圖層識別 (e.g., "district-boundary")
  type: string;            // "fill" | "circle" | "line" | "symbol"
  paint: any;              // Mapbox paint 屬性
  property: any[];         // 資料欄位定義
  title: string;           // 圖層名稱
  source: string;          // GeoJSON 來源 Key
};

type MapFilter = {
  mode: "byParam" | "byLayer"; // 篩選模式
  byParam: { xParam: string; yParam: string; } | null;
};
```