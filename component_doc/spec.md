# Create Component

- 圖表類型
  - component_chart
    # 圖表配置
    為了正確地呈現圖表，需要將圖表配置填入組件配置中的`chart_config`參數，詳細內容請參閱[這篇先前的文章](https://citydashboard.taipei/documentation/front-end/introduction-to-components#component-configuration)。完整的圖表配置(Object)如下所示。
    ```json
    content_paste"chart_config": {
        "color": ["#9c7a3e", …], // Array of Strings; 至少填入一個hex色碼
        "types": ["BarPercentChart", …], // Array of Strings; 填入 1-3 個圖表名稱（英文名）
        "unit": "棟", // String || null; 資料的單位
        "categories": [], // Array of Strings || null; 呼叫 API 時會自動填入
    },
    ```
    [**`DB`** `dashboardmanager.component_charts`](https://citydashboard.taipei/documentation/back-end/components-db)
    在資料庫中，圖表配置分開儲存於 `component_charts` table ，並在呼叫 API 時與 `components` table 結合。
    # 圖表類型
    每個圖表的 Vue 元件位於 `/src/dashboardComponents/components` 資料夾中。對於使用 Apexcharts 呈現的圖表，它們各自的 Vue 元件都包含一個 `chartOptions` 物件，可以填入各種[Apexcharts 參數](https://apexcharts.com/docs/options/annotations/)。有些圖表 Vue 元件還包含清理函式(parsing functions)，用於清理圖表資料。這樣可以增加圖表之間的互通性，使相同的資料集可以呈現多種不同的圖表類型。
    以下是所有圖表類型的英文和中文名稱的參照。
    ```jsx
    content_paste{
        BarChart: "橫向長條圖",
        BarPercentChart: "長條圖(%)",
        ColumnChart: "縱向長條圖",
        DonutChart: "圓餅圖",
        GuageChart: "量表圖",
        RadarChart: "雷達圖",
        TimelineSeparateChart: "折線圖(比較)",
        TimelineStackedChart: "折線圖(堆疊)",
        TreemapChart: "矩形圖",
        DistrictChart: "行政區圖",
        MetroChart: "捷運行駛圖",
        HeatmapChart: "熱力圖",
        PolarAreaChart: "極座標圖",
        ColumnLineChart: "長條折線圖",
        BarChartWithGoal: "長條圖(目標)",
        IconPercentChart: "圖示比例圖",
        IndicatorChart: "指標圖",
        TextUnitChart: "文字單位圖"
    };
    ```
    > **資訊 - 1**
    >
    > 圖表在程式庫中都是使用英文 Pascal Case，而在使用者介面中顯示的圖表名稱則為其中文名。
    >
    > 英文-中文對照檔案位於 `/src/assets/configs/apexcharts` 資料夾中，名為 `chartTypes.js`。
    ### 橫向長條圖
    橫向長條圖通常用於需要呈現多筆條列資料的情況。
    ### 長條圖(%)
    長條圖(%)用於呈現百分比值，相較於量表圖更為簡潔。
    ### 縱向長條圖
    縱向長條圖用於顯示項目列表，最適合呈現12個以下的數據項目。當數據項目超過12個時，圖表會自動提供滾動功能以便查看更多資料，同時上方會出現工具列，使用者可藉此操作項目的縮放。
    ### 圓餅圖
    圓餅圖用於顯示列表項目的百分比值。預設情況下，列表項目按降序排列。如果列表包含超過 6 個項目，其餘項目將被合併為「其他」。
    ### 量表圖
    量表圖以圓形格式呈現百分比值。如果有多個系列(series)，將計算系列之間的平均百分比值並顯示在中央。
    ### 雷達圖
    雷達圖以圓形格式顯示系列內的各值差異。
    ### 折線圖(比較)
    折線圖(比較)用於顯示時間資料。每個系列獨立呈現。
    ### 折線圖(堆疊)
    折線圖(堆疊)用於顯示時間資料。每個系列將被堆疊呈現合計值。
    ### 矩形圖
    矩形圖用於以不同大小的矩形來呈現每個數據點相對於總數的值。
    > **小撇步 - 1**
    >
    > 本專案僅使用矩形圖來視覺化土地面積資料。
    ### 捷運行駛圖
    捷運行駛圖顯示給定捷運路線捷運車廂的壅擠程度。顏色越深，車廂越擁擠。捷運行駛圖使用 2D 數據呈現，但需要以特殊 key-value 格式，如下所示。
    ```json
    content_paste{
          "data": [
            {
                "data": [
                    {
                        // {{ ID 遞升 (A) 或遞減 (D) }} + {{車站 ID (同北捷官方)}}
                        "x": "AR13",
                        // 每個號碼代表一個車廂的擁擠程度 (1-4)
                        "y": 222222
                    },
                    {
                        "x": "DR11",
                        "y": 111122
                    },
                    {
                        "x": "AR15",
                        "y": 111122
                    },
                    {
                        "x": "AR10",
                        "y": 121121
                    },
                    ...
                ]
            }
          ]
    }
    ```
    ### 行政區圖
    行政區圖用於顯示 key 為雙北各行政區的列表。預設情況下，越大的數值會越不透明。
    ### 熱力圖
    熱力圖用於顯示三維資料，以網格形式呈現，並依據網格值的高低呈現不同顏色。
    ### 極座標圖
    極座標圖用於顯示三維資料，以數個扇形組成。
    ### 長條折線圖
    長條折線圖用來呈現時間資料。第一個系列以長條圖呈現，第二個系列則以折線圖呈現。
    ### 長條圖(目標)
    長條圖(目標)為一般的長條圖增加一個維度，顯示每個類別的目標值。
    ### 圖示比例圖
    圖示比例圖以兩種不同的圖示的陣列呈現百分比資料。
    ### 指標圖
    指標圖用來顯示數值是否在特定範圍內。圖表會根據數值顯示不同的顏色。指標圖使用 3D 資料呈現，但需要特殊格式的 key、子類別和值，如下所示。
    ```json
    content_paste{
        // A: 0-10, B: 11-20, C: 21-30
        "categories": ["A", "B", "C"],
        "data": [
            {
                "name": "I", // I 的值是 9 因此屬於 A 類
                // A 類的位置應填入 9
                // 其餘類別位置應填入 0
                "data": [9, 0, 0],
            },
            {
                "name": "II",
                "data": [0, 15, 0],
            }
        ]
    }
    ```
    ### 文字單位圖
    文字單位圖用於清晰展示數值及其對應的文字描述與單位。此圖表根據chart_config中設定的三種顏色，依序分別應用於文字描述、數值及單位的顯示。雖然文字單位圖採用3D數據結構，但它特別利用icon欄位來呈現單位符號或其他補充說明，為數據提供更完整的上下文。使用範例如下：
    ```json
    content_paste{
        // categories欄位在此圖表類型中不需使用
        "categories": [""],
        "data": [
            {
                "name": "扶養比", // 文字描述部分
                "data": [49], // 數值部分
                "icon": "%" // 單位或補充說明部分
            },
            {
                "name": "老化指數",
                "data": [219],
                "icon": "%"
            }
        ]
    }
    ```
- **空間資料樣式**
  - geojson
    本專案支援透過本地 `geojson` 或透過圖磚服務 (map tiling server)（如 [Geoserver](https://geoserver.org/)）來渲染地圖。
    所有常見的幾何類型均有支援：`Point`（點）、`LineString`（線）、`Polygon`（多邊形）、`MultiPoint`（多點）、`MultiLineString`（多線）、以及 `MultiPolygon`（多多邊形）。建議每個幾何物件中也包含幾個屬性資料(properties)，以便在點擊地圖上的數據點時能顯示額外資訊。
    > **資訊 - 1**
    >
    > 我們仍在努力將我們的 Geoserver 設定開源。因此，對於希望貢獻本專案的外部開發者，目前僅支援本地 `geojson` 檔案。
    >
    > 如果您正在開發自己的專案，歡迎您配置一個動態圖磚服務（如 Geoserver 或 MapBox），並修改 `mapStore` 以從您自己的服務中獲取資料。
- 地圖類型
  - map config
    # 地圖配置
    為讓每個組件可以包含數個地圖圖層，地圖配置的形式為 Array ，清單的每個項目即為一個圖層的設定。當在地圖頁面展開組件時，所有附屬於該組件的地圖將同時被呼叫並渲染。
    以下是完整的地圖配置物件。
    ```json
    content_paste"map_config": [
        {
            // String; 必須是唯一的並與地圖資料之檔案名稱相同
            "index": "socl_welfare",
            // Object; 支援所有 Mapbox 的Paint屬性。詳情參見第一個資訊框。
            "paint": {
                "fill-color": [] // 詳見第一個警告框。
            },
            "property": [
                // key: String; 地圖資料中的屬性名稱
                // name: String; 在使用者介面中顯示的名稱
                // mode: "video" || null; 是否嵌入影片或圖片
                { "key": "vil", "name": "里界" },
                { "key": "cnt_low_income", "name": "低收入人口數" },
                { "key": "video_url", "name": "影片連結", "mode": "video"}
            ], // Array of Objects; 在地圖的彈出式視窗中顯示的屬性
            "title": "社福人口", // String; 地圖名稱
            "type": "fill", // String; 輸入 8 種任一種可用的地圖類型
            "size": null, // String || null; 額外預設樣式設定，參見下一節
            "icon": null, // String || null; 額外預設樣式設定，參見下一節
            "source": "raster", // "raster" || "geojson"
            "city": // taipei || metrotaipei; 資料所屬城市
        },
        …
    ],
    ```
    [**`DB`** `dashboardmanager.component_maps`](https://citydashboard.taipei/documentation/back-end/components-db)
    在資料庫中，圖表配置分開儲存於 `component_maps` table ，並在呼叫 API 時與 `components` table 結合。
    > **資訊 - 1**
    >
    > 在 Mapbox 中，每個地圖類型均支援數個 Paint 屬性，用於控制地圖視覺呈現，如顏色、大小、模糊度等。如要微調地圖的預設形式，只需傳遞任何 Mapbox 支援的 Paint 屬性即可。 ([Mapbox 圖層文件](https://docs.mapbox.com/mapbox-gl-js/style-spec/layers/))
    > **警告 - 1**
    >
    > 除了指定非內建地圖類型外，各地圖類型的顏色預設皆為黑色，因此地圖類型的顏色 Paint 屬性(e.g `fill-color`, `circle-color`, etc.)都應該被指定。
    # 地圖類型
    本專案支援多種地圖類型。每個地圖類型都有預設的樣式，相關設定位於 `/src/assets/configs/mapbox` 的 `mapConfig.js` 檔案中。有些地圖亦支援一些預設變形。這可以透過在地圖配置中指定大小(size)或圖示(icon)參數來實現。
    ### Circle
    Circle 地圖類型在地圖上將點(Point)渲染為圓圈。`size`變化包括 `small` 和 `big`。`icon`變化包括 `heatmap`，此效果在地圖拉遠時會將點變模糊，形成類似熱力圖的效果。
    ### Fill
    Fill 地圖類型在地圖上渲染多邊形(Polygon)。沒有預設變化。
    ### Fill-extrusion
    Fill-extrusion 地圖類型從地圖上突出顯示多邊形(Polygon)的 3D 渲染。沒有預設變化。
    ### Line
    Line 地圖類型在地圖上渲染線條(Line)。`size`變化包括 `wide`。`icon`變化包括 `dash`，呈現虛線而不是實線。
    ### Symbol
    Symbol 地圖類型在地圖上將點(Point)渲染為圖示。如使用 symbol 地圖，必須將`icon`參數傳遞給地圖配置。目前可用的圖示包括 `metro`、`metro-density`、`triangle_green`、`triangle_white`、`youbike`、`bus` 和 `cctv`。
    ### Symbol-3d
    Symbol-3d 地圖類型在地圖上將點(Point)渲染為三維模型，現階段僅供三維捷運動態地圖使用。技術核心為透過 mapbox 結合 three.js ，依 geoserver 所發布之即時位置進行動態渲染。Symbol-3d 地圖並不是 Mapbox 的內建地圖類型，故無法以 paint 屬性變換 3D 模型造型，但仍可以 icon 設定不同 3D 模型，或以 size 改變整體 3D 模型大小。
    ### Arc
    Arc 地圖類型在地圖上將線條(Line)渲染成立體曲線，Arc 地圖圖資的單一線條都只能包含兩個點，多餘點位均不會被渲染。Arc 地圖並不是 Mapbox 的內建地圖類型，因此只支援四個屬性，規格如下：
    ```json
    content_paste"paint": {
        "arc-color": ["#ffffff", "#f34523"], // Array of Strings;
        // 單色曲線僅需提供一個色碼; 雙色漸層請提供兩個色碼
        "arc-width": 4, // Number
        "arc-opacity": 0.5, // Number; 0-1
        "arc-animate": true, // Boolean; 預設為 false
    }
    ```
    ### Voronoi
    Voronoi 地圖類型將點(Point)渲染為沃羅諾邊界。本地圖種類的 paint 屬性、預設的樣式等與 line 地圖類型完全相同。
    ### Isoline
    Isoline 地圖類型將點(Point)渲染為等高線。每個點都必須對應到一個值(存於地圖屬性 properties)，地圖屬性的 key 預設為 `value` ，但可以藉由 `isoline-key` paint 屬性更改 (見下)。本地圖種類的 paint 屬性、預設的樣式等與 line 地圖類型完全相同。
    ```json
    content_paste"paint": {
        "isoline-key": "value", // String; 預設為 "value"
        "isoline-step": 2, // Number; 等高線間隔。預設為 2
        "isoline-min": 0, // Number; 最小值。預設為 0
        "isoline-max": 100 // Number; 最大值。預設為 100
        // ...其他 line paint 屬性
    }
    ```
- 地圖篩選
  - map filter
    地圖篩選功能讓使用者能透過圖表來篩選該組件的地圖圖層。如要在一個組件啟動地圖篩選，必須填寫組件配置的 `map_filter` 參數。下面展示了應該填入 `map_filter` 的詳細內容。
    ```json
    content_paste"map_filter": {
        "mode": "byParam", // Enum; ["byParam", "byLayer"] 下方將針對兩個模式進行說明
        "byParam": { // Object || null; 如果篩選模式是 "byParam" 則必填
            "xParam": "", // String || null; 用來篩選的地圖圖層屬性(property) id
            "yParam": "" // String || null; 用來篩選的地圖圖層屬性(property) id
        }
    }
    ```
    [**`DB`** `dashboardmanager.](https://citydashboard.taipei/documentation/back-end/components-db)query_chart`
    `map_filter` 物件直接儲存在 query_chart table 中。
    # 篩選模式
    ### 依各圖層中屬性 (By Param)
    By Param 模式依組件中各圖層中所存的屬性進行篩選。被篩選屬性的各個值需要與圖表 x 軸與 y 軸對應，並完全相同，本模式才能順利運作。
    ### 依地圖圖層 (By Layer)
    By Layer 模式依組件中各圖層的名稱篩選，開關各圖層。各圖層的名稱(title)需要與圖表 x 軸對應，並完全相同，本模式才能順利運作。
    # 運作機制
    在支援地圖篩選的圖表中，會定義一個名為 `selectedIndex` 的變數來儲存當前選定的資料點（如果沒有選定則為 `null`）。當用戶在圖表上點擊資料點時，會呼叫一個處理函數(handler function)，如果該資料點之前未被選定，則啟用篩選，如果之前已被選定，則關閉篩選。
    啟用篩選是透過呼叫 `mapStore` 的 `addByParamFilter` 或 `addByLayerFilter` 函式來達成的。關閉篩選是透過呼叫 `mapStore` 的 `clearByParamFilter` 或 `clearByLayerFilter` 函式來實現的。
    # 支援的圖表類型
    橫向長條圖(BarChart)、長條圖(%)(BarPercentChart)、縱向長條圖(ColumnChart)、行政區圖(DistrictChart)、圓餅圖(DonutChart)、量表圖(GuageChart)、地圖圖例(MapLegend)、矩形圖(TreemapChart)、熱力圖(HeatmapChart)、極座標圖(PolarAreaChart)。
- 歷史資料樣式
  - history config
    為了正確地呈現歷史軸，需要將歷史軸配置填入組件配置中的`history_config`參數，詳細內容請參閱[這篇先前的文章](https://citydashboard.taipei/documentation/front-end/introduction-to-components#component-configuration)。完整的圖表配置(Object)如下所示。
    ```json
    content_paste{
        "color": null, // Null || Array of Strings; 如為 null 則使用圖表顏色
        "range": ["halfyear_ago", "year_ago"], // Array of Strings; 從資料庫查詢的時間範圍
        "unit": "棟" // Null || String; 資料的單位; 如為 null 則使用圖表單位
    }
    ```
    [**`DB`** `dashboardmanager.query_charts`](https://citydashboard.taipei/documentation/back-end/components-db)
    `history_config`物件直接儲存在`query_charts` table 中。
    > **資訊 - 1**
    >
    > `range` 參數支援的時間區間為 `month_ago`、`quarter_ago`、`halfyear_ago`、`year_ago`、`twoyear_ago`、`fiveyear_ago` 或 `tenyear_ago`.
