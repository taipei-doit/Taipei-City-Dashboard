# Sustainable Environment Idea: 雙北循環環境與生活品質治理

## 背景

本構想對應黑客松六大主題中的「Sustainable environment」。依 wiki，該主題涵蓋空氣品質、能源使用、排放、綠色設施、環境資源、環境指標與政策效果。

官方儀表板截圖中已經有以下相關組件，本提案刻意避開：

- 公園綠地、田園城市、行道樹
- 溫室氣體排放統計
- 用電量統計
- 空氣品質
- 節能輔導累計家數、累計節約電量、累計減碳量
- YouBike 使用情況與 YouBike 2.0 週間群像

本題不重做既有的「空氣、碳、電、綠地」視角，而是從市民日常可感知的「垃圾與回收服務、水環境品質、噪音壓力、環境稽查」切入，建立四個雙北組件。

## 建議題目

**雙北循環環境與生活品質治理儀表板**

核心問題：

- 雙北哪些行政區的垃圾、資源回收、廚餘收運服務密度不足？
- 雙北近年一般廢棄物產生量、資源垃圾量、廚餘量是否改善？
- 哪些河川、流域或行政區的水質指標需要優先關注？
- 噪音與環境稽查壓力集中在哪些城市、時段或污染類型？

## 雙北元件規則

四個組件都設計為雙北組件，支援：

- 城市範圍切換：臺北市、雙北合併。
- 圖表資料可依城市、行政區、年度或季度切換。
- 至少一個組件具備 map layer。此提案的第 1 個組件作為主要地圖圖層。

## 四個組件

### 1. 垃圾與回收服務覆蓋地圖

用途：

- 顯示臺北市、新北市、雙北合併範圍的垃圾車停靠點、資源回收/廚餘收運點、社區資收站或黃金資收站。
- 以行政區聚合服務密度，找出回收服務不足區、夜間服務缺口、週末收運缺口。
- 作為本主題必要的地圖圖層組件。

主要指標：

- 清運點數
- 資源回收收運日數
- 廚餘收運日數
- 資收站數
- 每平方公里服務點密度
- 每萬人口服務點密度

建議圖表：

- 地圖點圖：垃圾車/資收站點位。
- 行政區 choropleth：服務點密度。
- 橫向長條圖：行政區服務缺口排名。

資料來源：

- 臺北市垃圾車點位路線資訊
  - https://data.taipei/dataset/detail?id=6bb3304b-4f46-4bb0-8cd1-60c66dcd1cae
  - 格式：CSV
  - 欄位：行政區、里別、分隊、局編、車號、路線、車次、抵達時間、離開時間、地點、緯度、經度
  - 授權：公開
- 臺北市垃圾資源回收、廚餘回收限時收受點
  - https://data.taipei/dataset/detail?id=1acf38f3-1509-4cb1-898a-9b1d4f31a3af
  - 格式：CSV
  - 欄位：行政區、分隊、電話、地址、備註、緯度、經度
  - 授權：公開
- 臺北市社區資源回收站資訊
  - https://data.taipei/dataset/detail?id=32d5286a-deea-4ea4-9789-605705001d96
  - 格式：CSV
  - 欄位：編號、回收站名稱、行政區、行政區代碼、地址
  - 授權：公開
- 新北市垃圾車路線
  - https://data.ntpc.gov.tw/datasets/edc3ad26-8ae7-4916-a00b-bc6048d19bf8
  - 格式：JSON、CSV、XML
  - 欄位：行政區、路線編號、路線名稱、里、經度、緯度、表定時間、一般垃圾/回收/廚餘各星期收運欄位
  - 更新頻率：每日
  - 授權：政府資料開放授權條款-第 1 版
- 新北市黃金資收站資訊
  - https://data.ntpc.gov.tw/datasets/a381e1f4-86d0-4575-adb4-8d9b6a75e3c4
  - 格式：JSON、CSV、XML
  - 欄位：區別、里別、資收站地址、開放時段、營運狀態
  - 授權：政府資料開放授權條款-第 1 版

ETL 重點：

- 點位資料保留經緯度，沒有座標的資收站先以行政區聚合，不強制地理編碼。
- 新北垃圾車路線可由星期欄位計算一般垃圾、資源回收、廚餘每週服務頻率。
- 臺北垃圾車點位與限時收受點合併時，要以「服務類型」欄位區分一般垃圾、資源回收、廚餘、限時收受點。

### 2. 一般廢棄物與回收成效趨勢

用途：

- 比較臺北市、新北市一般廢棄物產生量、一般垃圾量、資源垃圾量、廚餘量的年度變化。
- 追蹤回收率與廚餘回收占比，評估資源循環政策效果。
- 搭配第 1 個地圖元件，觀察「服務覆蓋」與「回收成效」是否一致。

主要指標：

- 一般廢棄物產生量
- 一般垃圾量
- 資源垃圾量
- 廚餘量
- 資源垃圾占比
- 廚餘占比
- 雙北合計量與城市占比

建議圖表：

- 折線圖：年度趨勢。
- 堆疊長條圖：一般垃圾、資源垃圾、廚餘結構。
- 雙城市比較長條圖：臺北市 vs 新北市。

資料來源：

- 環境部「一般廢棄物清理情況資料」
  - https://data.moenv.gov.tw/dataset/detail/STAT_P_45
  - 政府資料開放平臺頁面：https://data.gov.tw/dataset/89022
  - 格式：CSV、JSON、XML
  - 欄位：Year、County、GarbageGenerated、GarbageClearance、GarbageRecycled、FoodWastesRecycled
  - 授權：依政府資料開放平臺使用規範
- 環境部「執行機關一般廢棄物產生量」
  - https://data.gov.tw/dataset/89040
  - 格式：CSV、JSON、XML
  - 欄位：統計期、統計區、總產生量、一般垃圾量、資源垃圾量、廚餘量、平均每人每日一般廢棄物產生量
  - 授權：政府資料開放授權條款-第 1 版
- 臺北市各區清潔隊資源回收量
  - https://data.taipei/dataset/detail?id=34f4f00b-5386-43ab-bcc7-b0ae7ee3e305
  - 格式：CSV
  - 欄位：年度、月、行政區域代碼、區隊、回收量（噸）
  - 授權：公開

ETL 重點：

- 環境部資料作為雙北城市層級主資料。
- 臺北市各區清潔隊資源回收量可做臺北行政區 drill-down；新北若沒有同等行政區量資料，雙北視圖先維持城市層級，避免用不可驗證推估值。
- 可補入人口或面積資料，計算每人每日一般廢棄物量與每平方公里產生量。

### 3. 河川水質風險追蹤

用途：

- 追蹤雙北河川測站水質狀態，包含 RPI、溶氧量、生化需氧量、氨氮、懸浮固體等。
- 比較不同流域、河川、行政區的污染壓力。
- 建立「近期水質異常」摘要，協助使用者快速看到哪一段河川需要關注。

主要指標：

- RPI 或污染等級
- 溶氧量
- 生化需氧量
- 氨氮
- 懸浮固體
- 大腸桿菌群
- 測站異常次數

建議圖表：

- 橫向長條圖：河川/測站污染指標排名。
- 時間序列：單一測站水質變化。
- 指標卡：最新月高風險測站數。

資料來源：

- 環境部「河川水質監測資料」
  - https://data.gov.tw/dataset/6078
  - 格式：CSV
  - 欄位：siteid、sitename、county、township、basin、river、twd97lon、twd97lat、sampledate、itemname、itemvalue、itemunit
  - 授權：政府資料開放授權條款-第 1 版
- 環境部「河川水質測點基本資料」
  - https://data.moenv.gov.tw/dataset/detail/WQX_P_06
  - 欄位：SiteId、SiteName、County、Township、Basin、River、TWD97Lon、TWD97Lat、SiteAddress、StatusOfUse
  - 授權：依政府資料開放平臺使用規範
- 臺北市河川水質檢測
  - https://data.taipei/dataset/detail?id=759db528-77b5-4aa3-b6fa-2b857890214e
  - 格式：CSV
  - 欄位：河川名稱、監測站、水溫、pH、溶氧量、生化需氧量、氨氮、懸浮固體、化學需氧量、重金屬、總磷、濁度、大腸桿菌群等
  - 更新頻率：每 1 月
  - 授權：公開

ETL 重點：

- 以環境部資料建立雙北一致欄位，篩選 County 為臺北市、新北市。
- 測項資料通常是 long format，寫入 ready table 前可保留 long format，前端查詢時依指標 pivot。
- 臺北市資料可作臺北測站補強，但不要讓臺北欄位獨有指標破壞雙北比較。

### 4. 噪音與環境稽查壓力

用途：

- 比較臺北市、新北市噪音監測合格率、不合格時段、噪音陳情、噪音稽查量。
- 區分日間、晚間、夜間，找出生活環境壓力最大的時段。
- 與第 1 個垃圾/回收服務地圖或交通資料搭配，分析夜間收運、道路交通、近鄰噪音等壓力來源。

主要指標：

- 環境音量合格率
- 日間/晚間/夜間不合格時段數
- 噪音陳情案件數
- 噪音稽查次數
- 噪音源類型分布
- 監測站數與啟用狀態

建議圖表：

- 堆疊長條圖：日間、晚間、夜間不合格時段。
- 折線圖：年度噪音稽查與陳情趨勢。
- 橫向長條圖：噪音源類型排名。

資料來源：

- 環境部「環境音量監測結果統計(依時段分)」
  - https://data.moenv.gov.tw/dataset/detail/nos_p_03
  - 欄位：Year_Quarter、County、Num_Test、Rate_Pass、Day_Num_Pass、Day_Rate_Pass、Eve_Num_Pass、Eve_Rate_Pass、Night_Num_Pass、Night_Rate_Pass
  - 授權：依政府資料開放平臺使用規範
- 環境部「環境音量監測不合格時段數」
  - https://data.moenv.gov.tw/dataset/detail/STAT_P_117
  - 欄位：item1、item2、value1、value2、value3、value4
  - 更新頻率：每 3 月
  - 授權：依政府資料開放平臺使用規範
- 環境部「噪音陳情案件數(依音源)」
  - https://data.moenv.gov.tw/dataset/detail/NOS_P_10
  - 欄位：year、county、擴音設備、固定動力、動力機具、機動車輛、道路、近鄰噪音、低頻噪音等音源類別
  - 授權：依政府資料開放平臺使用規範
- 環境部「噪音稽查次數」
  - https://data.moenv.gov.tw/dataset/detail/STAT_P_95
  - 欄位：ItemName、Category、Year、ItemUnit、ItemValue
  - 更新頻率：每 1 年
  - 授權：依政府資料開放平臺使用規範
- 臺北市環境及交通音量監測站地點
  - https://data.taipei/dataset/detail?id=e2f4ebf5-bffa-40af-8056-383893721731
  - 欄位：測點名稱、測點編號、測點地址、管制區類別、測點性質、經度、緯度
  - 授權：公開
- 新北市環境及交通噪音監測站地點
  - https://data.ntpc.gov.tw/datasets/cad88b80-8230-48d4-a8d4-ce478954fddf
  - 欄位：測點名稱、測點編號、測點位置、管制區類別、緊臨道路寬度_m
  - 更新頻率：每年
  - 授權：政府資料開放授權條款-第 1 版

ETL 重點：

- 監測站位置可作補充地理資料，但本主題地圖主元件仍建議放在第 1 個垃圾與回收服務覆蓋地圖。
- 環境部噪音統計資料可直接用縣市欄位建立雙北比較。
- 音源別欄位很多，建議在 ETL 轉成 long format：year、county、noise_source、case_count。

## 不與既有元件重疊的理由

- 不使用既有公園綠地、田園城市、行道樹資料作為主題。
- 不重做溫室氣體排放、用電量、節能輔導、節電量、減碳量。
- 不以空氣品質即時值作為主元件，避免和既有空氣品質組件重疊。
- 不使用 YouBike 或交通量作為主元件，避免和智慧交通既有畫面重疊。
- 本題核心是「循環資源服務、水質、噪音、稽查」，屬於永續環境但和截圖中的官方元件有清楚差異。

## AI Chat 整合方式

依 wiki，AI Chat 應由後端 gateway 串接指定模型，不應由前端直接呼叫模型。模型只負責解釋、比較與推薦，資料查詢由後端 tools 查詢 PostgreSQL prepared tables。

建議 AI tools：

### `get_environment_component_catalog()`

用途：

- 回傳四個永續環境組件的 id、名稱、支援城市範圍、可用指標、是否有地圖圖層。

範例問題：

- 「幫我建立一個 Sustainable environment dashboard。」
- 「這個主題有哪些雙北元件？」

### `get_recycling_service_gap(city_scope, district, weekday)`

用途：

- 查詢指定城市範圍、行政區或星期的垃圾、回收、廚餘服務密度與服務缺口。

範例問題：

- 「雙北哪些區週末廚餘收運比較少？」
- 「板橋區和大安區的回收服務密度差多少？」

### `get_waste_trend(city_scope, metric, year_range)`

用途：

- 查詢一般廢棄物、一般垃圾、資源垃圾、廚餘量趨勢。

範例問題：

- 「雙北近五年資源垃圾量有增加嗎？」
- 「臺北和新北哪個城市廚餘占比比較高？」

### `get_river_water_quality_summary(city_scope, river, indicator)`

用途：

- 查詢指定河川或城市範圍的最新水質摘要、異常測站與歷史趨勢。

範例問題：

- 「淡水河流域最近哪個測站水質最需要注意？」
- 「新北市氨氮偏高的測站有哪些？」

### `get_noise_pressure_summary(city_scope, period, source_type)`

用途：

- 查詢噪音合格率、不合格時段、陳情來源、稽查量。

範例問題：

- 「雙北夜間噪音壓力哪裡比較高？」
- 「噪音陳情主要來自道路還是近鄰噪音？」

### `recommend_environment_actions(user_goal, city_scope)`

用途：

- 依使用者目標推薦應查看的組件、排序與政策觀察重點。

範例問題：

- 「我想改善夜間生活品質，該看哪些指標？」
- 「如果要提高回收率，應先補哪些區？」

## Demo 敘事建議

1. 使用者問 AI：「幫我做一個雙北永續環境 dashboard，不要空氣品質和用電。」
2. AI 呼叫 `get_environment_component_catalog()`，推薦四個本題組件。
3. 使用者點開「垃圾與回收服務覆蓋地圖」，切到雙北合併，AI 呼叫 `get_recycling_service_gap()` 說明服務缺口行政區。
4. 使用者追問：「這些區回收成效也比較差嗎？」AI 呼叫 `get_waste_trend()` 比較一般廢棄物與資源垃圾趨勢。
5. 使用者改問：「河川或噪音還有沒有風險？」AI 分別呼叫 `get_river_water_quality_summary()` 與 `get_noise_pressure_summary()`，回傳最需要關注的流域、時段與音源。
6. Dashboard 最後由 AI 產出「優先改善建議」：補強回收服務、觀察水質異常測站、針對夜間噪音來源安排稽查。

## MVP 優先順序

Day 1 建議先做：

1. 垃圾與回收服務覆蓋地圖
2. 一般廢棄物與回收成效趨勢
3. `get_environment_component_catalog()`
4. `get_recycling_service_gap()`

Day 2 再補：

1. 河川水質風險追蹤
2. 噪音與環境稽查壓力
3. `get_waste_trend()`
4. `get_river_water_quality_summary()`
5. `get_noise_pressure_summary()`
6. Demo 用的 `recommend_environment_actions()`

## 資料可取得性結論

四個組件都有公開、合法、可驗證資料可用：

- 地圖資料：臺北垃圾車點位、新北垃圾車路線都有經緯度；臺北限時收受點也有經緯度。
- 雙北比較：環境部一般廢棄物、水質、噪音資料都有縣市欄位，可篩選臺北市與新北市。
- 行政區分析：垃圾車路線、資收站、河川水質測點可支援行政區或測站層級分析；回收量若新北缺行政區量資料，MVP 可先做城市層級比較。
- AI Chat：所有查詢都可由後端 tool 對內部 PostgreSQL prepared tables 查詢，不需要模型直接碰外部 API。
