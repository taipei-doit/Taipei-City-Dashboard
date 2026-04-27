# Disaster Resilience Idea: 雙北防災韌性資源與應變壓力

## 背景

本構想對應黑客松六大主題中的「Disaster resilience」。依 wiki，該主題涵蓋天氣、水文、風險區、歷史災害分布、告警、避難與應變資源。

官方儀表板已經有以下相關組件，本提案刻意避開：

- 各降雨強度分級淹水面積
- 狹小巷弄程度分佈
- 防空避難設施
- 透水鋪面
- 屋齡分布
- 水位監測
- 降雨淹水模擬圖
- 山坡地風險地點
- 海砂屋
- 抽水站狀態

本題不重做淹水、水位、抽水站、山坡地、建物風險或避難設施點位，而是從「災前資源配置、通報壓力、災後救助負擔、疏散資訊可近用性」切入，建立四個雙北組件。

核心問題：

- 颱洪來臨前，雙北哪些區域有足夠的臨時停車避災資源？
- 災害或緊急事件發生時，119 通報系統的負載趨勢如何？
- 長期來看，臺北市與新北市的災害救助壓力差異在哪裡？
- 各里是否具備可取得、可理解的疏散避難資訊？
- AI Chat 能否依使用者情境自動組合防災儀表板並解釋優先補強區域？

## 建議題目

**雙北防災韌性資源與應變壓力儀表板**

所有組件都必須是雙北組件，支援：

- `臺北市`：只看臺北市。
- `雙北`：臺北市與新北市合併或比較。

若資料格式不完全一致，元件的雙北比較應採用共同欄位，城市各自的細節欄位則放在 tooltip、補充表格或 AI 解釋中。

## 四個組件

### 1. 颱洪期間緊急停車資源

用途：

- 顯示颱風、洪水期間可供車輛移置或臨時停放的學校、路段或防汛停車範圍。
- 作為本主題的主要地圖圖層組件。
- 協助判斷災前車輛移置資源是否集中在少數行政區。

主要指標：

- 開放停車點數
- 可停車路段數
- 汽車容量
- 機車容量
- 行政區資源密度
- 資料更新時間

雙北共同欄位建議：

- `city`
- `district`
- `resource_name`
- `resource_type`：school、road、flood_parking_area
- `car_capacity`
- `motorcycle_capacity`
- `geometry_type`：point、line、polygon、district_summary
- `source_url`
- `updated_at`

資料來源：

- 臺北市颱風期間開放停車學校一覽表
  - 資料頁：https://data.taipei/dataset/detail?id=98a24a7b-48c7-4067-844e-de609d875190
  - 格式：CSV
  - 可用欄位：項次、學校名稱、行政區、汽車數、機車數
  - 授權：公開
- 臺北市颱風與洪水期間緊急停車規定與範圍
  - 資料頁：https://data.taipei/dataset/detail?id=d5dd66c9-595a-47bc-ae18-c9ac62549664
  - 格式：SHP
  - 可用欄位：道路名稱、道路編碼、道路分類、幾何圖資
  - 授權：公開
- 新北市境內颱風期間可供停車之路段一覽表
  - 資料頁：https://data.ntpc.gov.tw/datasets/e3c0e87e-dcdb-41fc-9f21-38402dde2ad9
  - 格式：JSON、CSV、XML
  - 授權：政府資料開放授權條款-第 1 版

地圖圖層設計：

- 臺北學校資料若只有地址或行政區，第一版可用行政區聚合呈現；若補上座標，改為 point layer。
- 臺北防汛道路 SHP 轉為 GeoJSON line layer。
- 新北可停車路段以 line layer 呈現；若資料缺座標，先以行政區摘要圖呈現。
- 圖層 legend 可分為「學校開放停車」、「防汛道路」、「颱風開放停車路段」。

AI Chat 結合：

- 使用者問「颱風來前哪裡停車避災資源不足？」時，AI 查詢各行政區資源密度、容量與資料完整度。
- AI 可自動推薦本元件作為地圖主圖層，並搭配歷史災害救助與疏散資訊覆蓋率。
- 回答需標明資料限制：臺北與新北資料型態不同，路段容量可能不一定完整。

### 2. 119 接報負載趨勢

用途：

- 比較臺北市與新北市 119 接報或救災救護指揮中心電話量。
- 呈現緊急通報系統長期負載趨勢。
- 作為災害應變壓力的代理指標。

主要指標：

- 年度 119 受理電話量
- 年度變化率
- 每萬人接報量
- 臺北進線方式結構
- 雙北接報量占比

雙北共同欄位建議：

- `city`
- `year`
- `call_volume`
- `call_volume_per_10k_population`
- `source_url`
- `updated_at`

臺北延伸欄位：

- `valid_mobile_calls`
- `invalid_mobile_calls`
- `valid_landline_calls`
- `invalid_landline_calls`
- `sms_reports`
- `fax_reports`

資料來源：

- 臺北市政府消防局119受理電話分析統計
  - 資料頁：https://data.taipei/dataset/detail?id=67674cb5-06ae-4314-b1c5-5bdef898a6e0
  - 格式：CSV
  - 可用欄位：年度、有效行動電話數量、無效行動電話數量、有效市內電話數量、無效市內電話數量、簡訊報案數量、傳真報案數量、總計數量
  - 授權：公開
- 新北市政府消防局救災救護指揮中心受理電話量
  - 資料頁：https://data.ntpc.gov.tw/datasets/3640207c-eb19-4f8f-a180-37b20dd872cd
  - 格式：JSON、CSV、XML
  - 可用欄位：year、call_volume
  - 授權：政府資料開放授權條款-第 1 版

地圖圖層設計：

- 本元件本身以時間序列與城市比較為主，不一定需要地圖。
- 可附加行政區人口底圖作 normalization 說明，但第一版不建議強行做地圖，避免資料粒度不足。

AI Chat 結合：

- 使用者問「雙北哪邊通報壓力較高？」時，AI 以共同欄位 `call_volume` 比較。
- 使用者問「臺北 119 通報主要來自哪種方式？」時，AI 可讀臺北延伸欄位，但需說明新北無相同細項。
- AI 可將本元件推薦到「災害應變中」情境包。

### 3. 歷史災害救助與災損衝擊

用途：

- 觀察臺北市與新北市長期災害救助、收容、安遷與救助金額趨勢。
- 衡量災後復原壓力與資源投入。
- 支援災後檢討與政策資源分配。

主要指標：

- 災害次數
- 臨時收容災民數
- 死亡、失蹤、重傷人數
- 安遷救助戶數
- 安遷救助人數
- 財物受損影響生計戶數
- 救助金額

雙北共同欄位建議：

- `city`
- `period`
- `disaster_count`
- `shelter_count`
- `temporary_sheltered_people`
- `affected_people_total`
- `death_count`
- `missing_count`
- `serious_injury_count`
- `relocation_households`
- `relocation_people`
- `livelihood_affected_households`
- `relief_amount`
- `source_url`
- `updated_at`

資料來源：

- 臺北市遭受災害救助情形
  - 資料頁：https://data.taipei/dataset/detail?id=a6046af0-7160-449c-a94c-2270a62bc305
  - 格式：CSV
  - 收錄期間：1996-01-01 至 2024-12-31
  - 可用欄位：統計期、受災次數、臨時收容災民、死亡、失蹤、重傷、房屋毀損、收容所、安遷救助、財物受損影響生計者、救助金額
  - 授權：公開
- 新北市遭受災害救助情形
  - 資料頁：https://data.ntpc.gov.tw/datasets/05e9a748-13c6-4fd0-babb-ab48024e7f49
  - 格式：JSON、CSV、XML
  - 可用欄位：期間、災害次數、收容所、臨時收容災民數、受災人數、死亡、失蹤、重傷、安遷救助、財物受損影響生計者、救助金額
  - 授權：政府資料開放授權條款-第 1 版

地圖圖層設計：

- 資料以城市或年度統計為主，第一版不做細地圖。
- 可與行政區人口或城市邊界做 choropleth，但核心仍是 time series 與雙北比較。

AI Chat 結合：

- 使用者問「臺北和新北哪邊災害救助壓力比較高？」時，AI 比較共同欄位與每萬人標準化結果。
- 使用者問「近年救助金額是否上升？」時，AI 查時間序列並回覆趨勢。
- AI 可將本元件推薦到「災後檢討」與「長期韌性評估」情境包。

### 4. 里級疏散資訊覆蓋率

用途：

- 評估各里是否有可取得的疏散避難圖、防災地圖或優先避難排序資訊。
- 重點是「資訊覆蓋與可近用性」，不是避難設施點位。
- 協助找出需要補強防災溝通與資料發布的行政區。

主要指標：

- 有疏散圖里數
- 有防災地圖行政區數
- 有優先避難排序里數
- 覆蓋率
- 多語版本數
- 缺資料里數

雙北共同欄位建議：

- `city`
- `district`
- `village`
- `area_code`
- `has_evacuation_map`
- `has_disaster_map`
- `has_priority_shelter_order`
- `language`
- `file_url`
- `coverage_score`
- `source_url`
- `updated_at`

資料來源：

- 臺北市各區各里簡易疏散避難地圖資訊
  - 中山區範例：https://data.taipei/dataset/detail?id=c259b18c-2146-4531-aadc-3e1da7a5d9ed
  - 中正區範例：https://data.taipei/dataset/detail?id=9f9bdad6-948d-45d7-bca6-a807f8b0682e
  - 內湖區範例：https://data.taipei/dataset/detail?id=00880bf8-8f57-4929-a7f8-a7c954685013
  - 信義區範例：https://data.taipei/dataset/detail?id=ed642d05-1b2b-42eb-a679-838f8a689350
  - 松山區範例：https://data.taipei/dataset/detail?id=7c9b715c-67ae-4012-84ad-af401c688145
  - 北投區範例：https://data.taipei/dataset/detail?id=d76ca4fd-55ad-48c6-8ba1-18a2ffd3ac24
  - 大安區範例：https://data.taipei/dataset/detail?id=c00e0b69-e420-4e5b-a306-25079b7eacde
  - 士林區範例：https://data.taipei/dataset/detail?id=4f58b1f2-f8ac-4f97-908b-a1303f57625e
  - 格式：CSV
  - 可用欄位：District、AreaCode、Village、Language、FILE_URL
  - 授權：公開
- 新北市各區防災地圖
  - 資料頁：https://data.ntpc.gov.tw/datasets/842d0887-071f-4f67-aeb5-7da724004703
  - 格式：JSON、CSV、XML
  - 說明：新北市各區防災地圖 GIS 網址清單
  - 授權：政府資料開放授權條款-第 1 版
- 新北市避難收容處所優先排序自主檢核表
  - 資料頁：https://data.ntpc.gov.tw/datasets/e49bcba9-47d0-436d-90cd-1f4ef12ec5c6
  - 格式：JSON、CSV、XML
  - 可用欄位：行政區域、里名、優先排序1、優先排序2、優先排序3
  - 授權：政府資料開放授權條款-第 1 版

地圖圖層設計：

- 使用里界或行政區界做 fill layer，依 `coverage_score` 著色。
- 不顯示避難收容處所點位，避免與官方現有避難設施重疊。
- Popup 顯示該里是否有疏散圖、語言版本、是否有優先避難排序與資料連結。
- 若第一版里界資料整合成本過高，可先做行政區層級 coverage map。

AI Chat 結合：

- 使用者問「哪些地方疏散資訊最不完整？」時，AI 回傳 coverage score 最低的行政區或里。
- 使用者問「我住在某區，能看什麼防災資訊？」時，AI 回傳該區/里的疏散圖或防災地圖連結。
- 使用者問「這不是已經有避難設施了嗎？」時，AI 應說明本元件評估的是資訊覆蓋，不是設施容量或點位。

## 資料可取得性結論

四個組件都有公開、合法、可驗證資料可用：

- 颱洪期間緊急停車資源：臺北與新北皆有公開資料，但資料型態不同，需正規化。
- 119 接報負載趨勢：雙北皆有年度接報量，可做共同欄位比較。
- 歷史災害救助與災損衝擊：雙北欄位高度接近，是最穩定的雙北比較元件。
- 里級疏散資訊覆蓋率：臺北資料分散在各區，新北有防災地圖與優先排序資料，整理成本較高但創意與應用價值高。

最穩定 MVP 順序：

1. 歷史災害救助與災損衝擊。
2. 119 接報負載趨勢。
3. 颱洪期間緊急停車資源。
4. 里級疏散資訊覆蓋率。

## AI Chat 整合方式

依 wiki，AI Chat 應由後端 gateway 串接 TWCC 模型，不應由前端直接呼叫模型。指定模型為 `llama3.3-ffm-70b-16k-chat`。後端可透過 tool calling 執行資料查詢，並將互動寫入 `ai_chatlog`。

本題的 AI Chat 應定位為「防災情境助理」，負責：

- 依自然語言判斷防災情境。
- 自動推薦或組合四個雙北組件。
- 查詢內部資料表取得摘要、排行與比較。
- 解釋資料限制與更新時間。
- 控制 dashboard 城市範圍：臺北市或雙北。

AI 不應直接即時呼叫外部資料源，也不應生成未經資料支持的數字。

建議流程：

1. Airflow ETL 從 data.taipei、data.ntpc.gov.tw 取得資料。
2. ETL 將不同來源欄位正規化，寫入 PostgreSQL。
3. Dashboard 元件查詢 PostgreSQL 呈現圖表與地圖。
4. AI Chat 透過後端 tools 查詢同一批內部資料表。
5. 模型根據 tool 查詢結果產生自然語言解釋、比較與建議。

## 建議 AI Tools

### `get_disaster_component_catalog()`

用途：

- 回傳四個防災韌性組件的 id、名稱、主題、可用指標、是否有地圖圖層、支援城市範圍。

範例問題：

- 「幫我準備一個雙北防災 dashboard。」
- 「這個主題有哪些元件可以看？」

### `get_disaster_component_summary(component_id, city_scope, district)`

用途：

- 查詢指定組件在臺北市或雙北範圍的摘要資料。
- `city_scope` 可為 `taipei` 或 `metro_taipei`。

範例問題：

- 「雙北颱風停車資源最多的是哪些區？」
- 「臺北市近年災害救助金額趨勢如何？」

### `compare_disaster_metric(metric, city_scope, normalize_by_population)`

用途：

- 比較雙北共同指標，例如 119 接報量、災害次數、臨時收容人數、救助金額、疏散資訊覆蓋率。
- 支援是否用人口標準化。

範例問題：

- 「臺北和新北哪邊災害救助壓力較高？」
- 「雙北 119 接報量差距有多大？」

### `rank_disaster_districts(scenario, metric, limit)`

用途：

- 依情境輸出行政區排行。
- 情境可包含 `typhoon_preparation`、`emergency_response`、`post_disaster_review`、`evacuation_information_gap`。

範例問題：

- 「颱風前要優先補強哪些行政區？」
- 「哪些地方疏散資訊最不完整？」

### `recommend_disaster_dashboard(user_goal, city_scope)`

用途：

- 依使用者描述推薦組件組合與排序。
- 回傳可加入 dashboard 的 component ids、原因、建議城市範圍。

範例問題：

- 「我要做災前整備，幫我挑元件。」
- 「我要做災後檢討，應該看哪些圖？」

## AI Chat 展示情境

### 情境 1：颱風前整備

使用者：

```text
颱風來前，幫我準備一個雙北防災儀表板。
```

AI 行為：

- 呼叫 `recommend_disaster_dashboard(user_goal="typhoon preparation", city_scope="metro_taipei")`。
- 推薦「颱洪期間緊急停車資源」、「里級疏散資訊覆蓋率」、「歷史災害救助與災損衝擊」。
- 若需要應變壓力背景，再加入「119 接報負載趨勢」。

AI 回答應包含：

- 已選用哪些組件。
- 為何這些組件符合颱風前整備。
- 哪一個是地圖主圖層。
- 資料更新時間與限制。

### 情境 2：應變壓力比較

使用者：

```text
臺北和新北哪邊 119 通報壓力比較高？
```

AI 行為：

- 呼叫 `compare_disaster_metric(metric="call_volume", city_scope="metro_taipei", normalize_by_population=false)`。
- 視需要再呼叫人口標準化版本。

AI 回答應包含：

- 原始接報量比較。
- 每萬人接報量比較。
- 臺北有進線方式細項、新北只有總量的資料差異。

### 情境 3：災後復原壓力

使用者：

```text
近年雙北哪邊災害救助壓力比較大？
```

AI 行為：

- 呼叫 `compare_disaster_metric(metric="relief_amount", city_scope="metro_taipei", normalize_by_population=false)`。
- 呼叫 `compare_disaster_metric(metric="temporary_sheltered_people", city_scope="metro_taipei", normalize_by_population=false)`。

AI 回答應包含：

- 救助金額趨勢。
- 收容人數趨勢。
- 是否需要用人口或行政區面積標準化。
- 不應把救助金額直接解釋成災害嚴重度，因為制度與申請條件也會影響數字。

### 情境 4：疏散資訊缺口

使用者：

```text
哪些地方疏散資訊最不完整？
```

AI 行為：

- 呼叫 `rank_disaster_districts(scenario="evacuation_information_gap", metric="coverage_score", limit=10)`。
- 回傳 coverage score 低的行政區或里。

AI 回答應包含：

- 缺哪些資料：疏散圖、防災地圖、優先避難排序、多語版本。
- 提醒本元件評估資訊可近用性，不評估避難設施容量。

## 地圖圖層總結

本題至少有兩個適合地圖圖層的組件：

1. **颱洪期間緊急停車資源**
   - 優先作為 MVP 地圖圖層。
   - 可呈現 point、line 或行政區聚合。
   - 適合 demo，因為和颱風前整備情境直接相關。

2. **里級疏散資訊覆蓋率**
   - 適合作為第二個地圖圖層。
   - 以行政區或里界 fill layer 顯示覆蓋率。
   - 不呈現避難設施點位，避免與既有組件重疊。

119 接報負載與歷史災害救助以 chart 為主，不建議第一版強行地圖化。

## 風險與限制

- 臺北與新北資料欄位不完全一致，雙北比較必須先定義共同欄位。
- 臺北疏散避難圖資料分散於各區資料集，ETL 需要維護多個 dataset id。
- 新北部分資料標示為不更新，使用時需顯示資料更新時間。
- 颱洪停車資料可能有點位、路段、SHP、行政區摘要等不同型態，地圖需支援多 geometry 或先做行政區聚合。
- AI Chat 應查詢內部資料表，不應在使用者提問時即時打外部 API。
- AI 回答必須附帶資料來源、更新時間與限制，避免把不完整資料解讀成完整事實。

## 推薦 MVP

第一版先完成：

1. 歷史災害救助與災損衝擊雙北比較。
2. 119 接報負載趨勢雙北比較。
3. 颱洪期間緊急停車資源地圖與行政區統計。
4. 里級疏散資訊覆蓋率行政區統計，地圖可先做行政區層級。
5. AI Chat 支援「組防災 dashboard」、「雙北比較」、「行政區排行」、「資料限制說明」四類問題。
