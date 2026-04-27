# Cultural Inclusion Idea: 雙北文化近用與多元參與

## 背景

本構想對應黑客松六大主題中的「Cultural inclusion」。依 wiki，該主題涵蓋文化活動、觀光資源、群體參與、商圈與文化政策支持。

官方儀表板若已有一般景點、觀光人流或單純活動清單，本提案不重做「活動公告牆」，而是從「文化服務是否可近用、公共文化資源是否均衡、基層文化參與是否多元、文化政策支持是否集中」切入，建立四個雙北組件。

核心問題：

- 雙北哪些行政區文化場館、博物館、公共藝術與文化資產較集中或缺口較大？
- 近期藝文活動是否集中在少數行政區、少數類型或高票價活動？
- 街頭藝人與演藝團體的參與類型、性別與空間分布是否均衡？
- 藝文補助與文化政策資源是否能支撐地方文化多樣性？
- AI Chat 能否依使用者目標推薦文化路線、找出文化近用缺口，並解釋資料限制？

## 建議題目

**雙北文化近用與多元參與儀表板**

所有組件都必須是雙北組件，支援：

- `臺北市`：只看臺北市。
- `雙北`：臺北市與新北市合併或比較。

若臺北與新北欄位不完全一致，元件的雙北比較應採用共同欄位，例如城市、行政區、文化類型、數量、日期、地址、經緯度、資料來源與更新時間。城市各自的細節欄位可放在 tooltip、補充表格或 AI 解釋中。

## 四個組件

### 1. 文化資源與公共藝術分布地圖

用途：

- 顯示雙北文化資產、公共藝術、博物館與藝文場館的空間分布。
- 作為本主題的主要地圖圖層組件。
- 協助判斷文化資源是否集中於核心商圈、捷運密集區或少數行政區。

主要指標：

- 文化資源點位數
- 文化資產數
- 公共藝術件數
- 博物館與藝文場館數
- 每萬人文化資源數
- 每平方公里文化資源數
- 行政區資源密度

雙北共同欄位建議：

- `city`
- `district`
- `resource_name`
- `resource_type`：heritage、public_art、museum、venue
- `category`
- `address`
- `longitude`
- `latitude`
- `source_url`
- `updated_at`

資料來源：

- 臺北市文化資產
  - 資料頁：https://data.taipei/dataset/detail?id=46119295-2534-4ac9-82d5-5f4653ba15bb
  - 格式：CSV，另提供 JSON 介接
  - 可用欄位：個案名稱、資產類別、資產種類、所屬主管機關、所在地理區域、縣市別代碼
  - 授權：公開
- 新北市文化資產
  - 資料頁：https://data.ntpc.gov.tw/datasets/d8eb898f-6c59-4689-9191-48dbbef16606
  - 格式：JSON、CSV、XML
  - 可用欄位：name、affection、category、rank、yyyy、address
  - 授權：政府資料開放授權條款-第 1 版
- 臺北市公共藝術
  - 資料頁：https://data.taipei/dataset/detail?id=5d54376a-591d-431f-95cb-79d44f8228b2
  - 格式：JSON
  - 可用欄位：序號、行政區、設置完成年度、作品名稱、作者、作品類型、設置地址/地點、設置單位/管理單位
  - 授權：公開
- 新北市公共藝術
  - 資料頁：https://data.ntpc.gov.tw/datasets/47CCF63F-733F-422D-AB20-5B50E8A6F983
  - 格式：JSON、CSV、XML
  - 可用欄位：district、name、creator、year、place、address、type、material、manager
  - 授權：政府資料開放授權條款-第 1 版
- 臺北市藝文推廣處各場館開放時間
  - 資料頁：https://data.taipei/dataset/detail?id=51c0b43e-8c03-4085-8a9e-ae3301125780
  - 格式：CSV
  - 可用欄位：場館、空間、開放時間、地址、市話、分機
  - 授權：公開
- 新北市博物館家族清單
  - 資料頁：https://data.ntpc.gov.tw/datasets/df63a853-aba9-4ec1-bd28-e74459e5d5c5
  - 格式：JSON、CSV、XML
  - 可用欄位：title、location、areacode、localcallservice、wgs84ax、wgs84ay
  - 授權：政府資料開放授權條款-第 1 版

地圖圖層設計：

- 使用 point layer 呈現文化資產、公共藝術、博物館與場館。
- 若資料只有地址沒有經緯度，第一版可用行政區聚合 fill layer；後續再用既有地址清理工具補點。
- 圖層 legend 分為「文化資產」、「公共藝術」、「博物館/藝文場館」。
- 點擊 popup 顯示名稱、類型、地址、開放時間或管理單位、資料來源與更新時間。

AI Chat 結合：

- 使用者問「雙北哪裡文化資源最不足？」時，AI 查行政區文化資源密度與人口標準化結果。
- 使用者問「幫我找板橋到萬華附近的公共藝術和文化資產」時，AI 可依地圖點位與距離排序回覆。
- AI 回答需標明資料限制：部分資料只有地址或行政區，未補座標前不應宣稱精準點位。

### 2. 藝文活動可近性與票價結構

用途：

- 比較臺北與新北近期藝文活動的類型、地點、期間與票價資訊。
- 衡量免費或低門檻活動是否足夠、是否集中於少數行政區。
- 支援「週末活動推薦」、「親子/長者友善活動」、「免費活動」等情境。

主要指標：

- 活動數
- 活動類型分布
- 免費活動數與比例
- 有票價資訊活動比例
- 活動行政區分布
- 活動期間長度
- 活動資料更新時間

雙北共同欄位建議：

- `city`
- `district`
- `event_id`
- `event_name`
- `event_type`
- `start_date`
- `end_date`
- `venue`
- `address`
- `longitude`
- `latitude`
- `ticket_type`
- `ticket_price`
- `event_url`
- `source_url`
- `updated_at`

資料來源：

- 臺北市政府文化局文化快遞資訊
  - 資料頁：https://data.taipei/dataset/detail?id=9a7af75b-9abd-4ac1-b359-685fbd7dac23
  - 格式：JSON
  - 可用欄位：ID、Category、Caption、Company、StartDate、EndDate、TicketType、TicketPrice、Venue、City、Area、Address、Longitude、Latitude、RelatedLink
  - 授權：公開
  - 更新頻率：每 6 月
- 新北市政府文化局藝文活動
  - 資料頁：https://data.ntpc.gov.tw/datasets/781B822E-214A-4B9A-B4DB-32C9F4626D98
  - 格式：JSON、CSV、XML
  - 可用欄位：author、type、startdate、enddate、title、link、description、pubdate
  - 授權：政府資料開放授權條款-第 1 版
  - 更新頻率：每日
- 新北市藝遊
  - 資料頁：https://data.ntpc.gov.tw/datasets/20a3b141-b1c1-4b61-b36a-7569e8ce24b3
  - 格式：JSON、CSV、XML
  - 可用欄位：year_month、remarks、url
  - 授權：政府資料開放授權條款-第 1 版

地圖圖層設計：

- 本元件可選擇性連動第 1 個地圖圖層，依行政區或活動點位過濾。
- 臺北文化快遞已有經緯度，可直接作活動點位。
- 新北藝文活動若缺地址或座標，第一版用發布單位與描述解析行政區，或只納入城市/類型比較。

AI Chat 結合：

- 使用者問「這週末有哪些免費文化活動？」時，AI 查活動日期、票價與行政區。
- 使用者問「雙北藝文活動是不是都集中在市中心？」時，AI 比較行政區活動數與人口標準化結果。
- AI 應提醒新北活動資料不一定含座標或票價，不能把「未標票價」等同於免費。

### 3. 街頭藝人與演藝團體多元參與

用途：

- 比較雙北街頭藝人、演藝團體與展演場地的類型分布。
- 觀察表演、音樂、視覺藝術、工藝藝術等類型是否均衡。
- 以性別與團體/個人組成作為「群體參與」的可量化指標之一。

主要指標：

- 街頭藝人數
- 街頭藝人性別結構
- 街頭藝人類型分布
- 演藝團體數
- 演藝團體類型分布
- 展演場地數
- 每萬人展演場地數

雙北共同欄位建議：

- `city`
- `year`
- `participant_type`：street_artist、performing_group、venue
- `category`
- `gender`
- `count`
- `district`
- `address`
- `source_url`
- `updated_at`

資料來源：

- 臺北市政府文化局街頭藝人
  - 資料頁：https://data.taipei/dataset/detail?id=5e4db75d-734e-42b7-8284-df413aa8122a
  - 格式：JSON
  - 可用欄位：Type、Name、Project、Describe、Url、Stagename、Sex、Moblie、Email
  - 授權：公開
- 臺北市街頭藝人展演場地資訊
  - 資料頁：https://data.taipei/dataset/detail?id=2154ce42-42e6-4fdb-8356-d961cb2b0987
  - 格式：CSV
  - 可用欄位：項次、展演地、主管機關、市話、分機、開放時段、開放表演類型、申請方式
  - 授權：公開
- 臺北市演藝團體名冊
  - 資料頁：https://data.taipei/dataset/detail?id=f56e77c6-cc69-480c-8ba4-057fc7e1d8d6
  - 格式：CSV
  - 可用欄位：演藝團體名稱、申請類別、立案字號、團址、網址
  - 授權：公開
- 新北市街頭藝人
  - 資料頁：https://data.ntpc.gov.tw/datasets/ba47fc6f-1fee-41e7-ab71-c50f9b5211c8
  - 格式：JSON、CSV、XML
  - 可用欄位：permit_number、group_name、name、sex、type、item、remarks
  - 授權：政府資料開放授權條款-第 1 版
- 新北市街頭藝人展演場地
  - 資料頁：https://data.ntpc.gov.tw/datasets/c0cc9bd8-870d-454b-afaa-277fac536277
  - 格式：JSON、CSV、XML
  - 可用欄位：author、title、link、description、pubdate
  - 授權：政府資料開放授權條款-第 1 版
- 新北市演藝團體一覽表
  - 資料頁：https://data.ntpc.gov.tw/datasets/0d07db17-675d-4104-b809-62079bf061da
  - 格式：JSON、CSV、XML
  - 可用欄位：category、name、manager、date、address
  - 授權：政府資料開放授權條款-第 1 版
- 臺北市藝文館所及街頭藝人時間數列統計資料
  - 資料頁：https://data.taipei/dataset/detail?id=e417fca7-9a62-4f95-822e-4870ec1aa711
  - 格式：CSV
  - 可用欄位：統計期、藝文館所/館所數、藝文館所/參訪人次、演藝團體個數、街頭藝人/許可證有效證照數、街頭藝人/表演場地數
  - 授權：公開
- 新北市街頭藝人統計
  - 資料頁：https://data.ntpc.gov.tw/datasets/08f5cabf-9f7d-4870-8140-21c23597bfc4
  - 格式：JSON、CSV、XML
  - 可用欄位：年、團體組/個人組、音樂/美術/表演/技藝、男/女
  - 授權：政府資料開放授權條款-第 1 版

地圖圖層設計：

- 以 chart 為主，不強制做地圖。
- 展演場地若補齊地址座標，可與第 1 個地圖圖層合併為 cultural access layer。

AI Chat 結合：

- 使用者問「雙北街頭藝人參與類型有什麼差異？」時，AI 比較音樂、表演、視覺、工藝等類型。
- 使用者問「哪裡比較缺展演場地？」時，AI 查行政區展演場地數與人口標準化結果。
- AI 應避免用姓名或個資做不必要揭露，回覆以統計彙整為主。

### 4. 文化政策支持與地方文化組織

用途：

- 觀察文化補助、獎勵團隊、演藝團體、文化基金會等政策支持與組織基礎。
- 比較不同城市與行政區的文化組織密度與補助分布。
- 支援文化政策資源是否集中、哪些區域需要補強在地文化組織的討論。

主要指標：

- 藝文補助件數
- 核定補助金額
- 獎勵團隊數
- 演藝團體數
- 文化基金會數
- 行政區組織密度
- 補助金額與團體數比例

雙北共同欄位建議：

- `city`
- `year`
- `district`
- `organization_name`
- `organization_type`：performing_group、foundation、award_team、subsidy_recipient
- `category`
- `project_name`
- `approved_amount`
- `address`
- `source_url`
- `updated_at`

資料來源：

- 臺北市政府文化局藝文補助案
  - 資料頁：https://data.taipei/dataset/detail?id=3734ac48-c652-4ef8-b630-fb12ef63e56a
  - 格式：CSV
  - 可用欄位：年度、類別、補助對象、補助計畫名稱、核定補助金額
  - 授權：公開
- 臺北市年度演藝團隊徵選與獎勵計畫
  - 資料頁：https://data.taipei/dataset/detail?id=f4633446-7665-4e36-8377-d17babcad086
  - 格式：CSV
  - 可用欄位：獲選年度、團隊名稱、立案年度、登記地址、社群網址
  - 授權：公開
- 臺北市演藝團體名冊
  - 資料頁：https://data.taipei/dataset/detail?id=f56e77c6-cc69-480c-8ba4-057fc7e1d8d6
  - 格式：CSV
  - 可用欄位：演藝團體名稱、申請類別、立案字號、團址、網址
  - 授權：公開
- 新北市演藝團體一覽表
  - 資料頁：https://data.ntpc.gov.tw/datasets/0d07db17-675d-4104-b809-62079bf061da
  - 格式：JSON、CSV、XML
  - 可用欄位：category、name、manager、date、address
  - 授權：政府資料開放授權條款-第 1 版
- 新北市文化基金會一覽表
  - 資料頁：https://data.ntpc.gov.tw/datasets/0351d41c-ef33-44da-bc3c-a64af58ddb91
  - 格式：JSON、CSV、XML
  - 可用欄位：name、address
  - 授權：政府資料開放授權條款-第 1 版
- 新北市政府文化局辦理藝文展演活動統計
  - 資料頁：https://staging.data.ntpc.gov.tw/datasets/de5786e9-8d8e-4b92-bb28-12ebef4aceb7
  - 格式：JSON、CSV、XML
  - 可用欄位：title、url
  - 授權：政府資料開放授權條款-第 1 版

地圖圖層設計：

- 本元件以統計 chart 為主，不建議第一版強行地圖化。
- 若團址地址清理完成，可做行政區組織密度圖，但須避免把補助收件地址誤解為服務範圍。

AI Chat 結合：

- 使用者問「文化補助是否集中在少數團體或區域？」時，AI 查補助件數、金額與組織分布。
- 使用者問「哪個區的文化組織基礎薄弱？」時，AI 比較演藝團體、基金會、獎勵團隊與活動數。
- AI 應說明補助資料與組織登記地址不等於實際文化服務範圍。

## 資料可取得性結論

四個組件都有公開、合法、可驗證資料可用：

- 文化資源與公共藝術分布地圖：雙北皆有文化資產、公共藝術與場館/博物館資料；新北博物館資料含 WGS84 座標，臺北部分資料需補座標或先做行政區聚合。
- 藝文活動可近性與票價結構：臺北文化快遞欄位完整且含票價、地址、經緯度；新北藝文活動每日更新但欄位較簡，需要做文字解析與資料限制揭露。
- 街頭藝人與演藝團體多元參與：雙北皆有街頭藝人、展演場地、演藝團體資料；性別與類型可作參與多樣性統計。
- 文化政策支持與地方文化組織：臺北有補助案、年度演藝團隊、演藝團體；新北有演藝團體、文化基金會與藝文展演統計，可支撐政策支持與組織基礎比較。

最穩定 MVP 順序：

1. 文化資源與公共藝術分布地圖。
2. 藝文活動可近性與票價結構。
3. 街頭藝人與演藝團體多元參與。
4. 文化政策支持與地方文化組織。

## AI Chat 整合方式

依 wiki，AI Chat 應由後端 gateway 串接 TWCC 模型，不應由前端直接呼叫模型。指定模型為 `llama3.3-ffm-70b-16k-chat`。後端可透過 tool calling 執行資料查詢，並將互動寫入 `ai_chatlog`。

本題的 AI Chat 應定位為「文化近用助理」，負責：

- 依自然語言判斷使用者想找活動、文化路線、資源缺口或政策分布。
- 自動推薦或組合四個雙北組件。
- 查詢內部資料表取得摘要、排行、比較與附近點位。
- 解釋資料來源、更新時間、座標完整度與欄位差異。
- 控制 dashboard 城市範圍：臺北市或雙北。

AI 不應直接即時呼叫外部資料源，也不應生成未經資料支持的活動、票價、地址或推薦理由。

建議流程：

1. Airflow ETL 從 data.taipei、data.ntpc.gov.tw 取得資料。
2. ETL 將不同來源欄位正規化，寫入 PostgreSQL。
3. Dashboard 元件查詢 PostgreSQL 呈現圖表與地圖。
4. AI Chat 透過後端 tools 查詢同一批內部資料表。
5. 模型根據 tool 查詢結果產生自然語言解釋、比較與建議。

## 建議 AI Tools

### `get_culture_component_catalog()`

用途：

- 回傳四個文化包容組件的 id、名稱、主題、可用指標、是否有地圖圖層、支援城市範圍。

範例問題：

- 「幫我準備一個雙北文化包容 dashboard。」
- 「這個主題有哪些元件可以看？」

### `search_cultural_resources(city_scope, district, resource_type, near, radius)`

用途：

- 查詢文化資產、公共藝術、博物館、藝文場館與活動點位。
- `city_scope` 可為 `taipei` 或 `metro_taipei`。
- `near` 可接受行政區、地標或座標；若無座標，回傳行政區層級結果。

範例問題：

- 「板橋車站附近有哪些文化資源？」
- 「萬華有哪些公共藝術和文化資產？」

### `compare_cultural_access(metric, city_scope, normalize_by_population)`

用途：

- 比較雙北共同指標，例如文化資源數、活動數、免費活動比例、展演場地數、演藝團體數。
- 支援是否用人口或面積標準化。

範例問題：

- 「雙北哪五個行政區文化資源最不足？」
- 「臺北和新北活動可近性差在哪？」

### `rank_culture_districts(scenario, metric, limit)`

用途：

- 依情境輸出行政區排行。
- 情境可包含 `resource_gap`、`free_event_access`、`street_artist_participation`、`policy_support_gap`。

範例問題：

- 「哪裡最需要新增文化場館？」
- 「哪些行政區免費活動最少？」

### `recommend_culture_dashboard(user_goal, city_scope)`

用途：

- 依使用者描述推薦組件組合與排序。
- 回傳可加入 dashboard 的 component ids、原因、建議城市範圍。

範例問題：

- 「我要做文化近用分析，幫我挑元件。」
- 「我要設計一條雙北文化散步路線，應該看哪些圖？」

## AI Chat 展示情境

### 情境 1：文化近用缺口

使用者：

```text
雙北哪些地方文化資源最不足？
```

AI 行為：

- 呼叫 `compare_cultural_access(metric="resource_density", city_scope="metro_taipei", normalize_by_population=true)`。
- 呼叫 `rank_culture_districts(scenario="resource_gap", metric="resources_per_10k_population", limit=10)`。

AI 回答應包含：

- 文化資源密度最低的行政區。
- 該區缺的是文化資產、公共藝術、博物館或藝文場館。
- 哪一個地圖圖層可用來檢查空間分布。
- 資料座標完整度與更新時間。

### 情境 2：免費或低門檻活動推薦

使用者：

```text
這週末雙北有哪些免費藝文活動？
```

AI 行為：

- 呼叫 `search_cultural_resources(city_scope="metro_taipei", resource_type="event", near=null, radius=null)`。
- 篩選日期落在週末且 `ticket_type` 或 `ticket_price` 顯示免費的活動。

AI 回答應包含：

- 活動名稱、類型、日期、地點、連結。
- 若票價欄位缺失，標示「未提供票價」而不是免費。
- 可切換到活動可近性組件查看行政區分布。

### 情境 3：街頭藝人與展演場地

使用者：

```text
哪裡比較適合增加街頭藝人展演場地？
```

AI 行為：

- 呼叫 `compare_cultural_access(metric="busker_venues", city_scope="metro_taipei", normalize_by_population=true)`。
- 呼叫 `rank_culture_districts(scenario="street_artist_participation", metric="venues_per_10k_population", limit=10)`。

AI 回答應包含：

- 展演場地密度較低的行政區。
- 該區街頭藝人或演藝團體類型分布。
- 是否附近已有公共文化資源可搭配。

### 情境 4：文化政策支持檢視

使用者：

```text
文化補助和團體分布是不是集中在少數區？
```

AI 行為：

- 呼叫 `compare_cultural_access(metric="organization_density", city_scope="metro_taipei", normalize_by_population=false)`。
- 查詢補助件數、補助金額、演藝團體、文化基金會與年度演藝團隊分布。

AI 回答應包含：

- 資源集中程度。
- 補助金額與團體數是否一致。
- 登記地址不等於實際服務範圍的限制。

## 地圖圖層總結

本題至少有兩個適合地圖圖層的組件：

1. **文化資源與公共藝術分布地圖**
   - 優先作為 MVP 地圖圖層。
   - 可呈現 point layer 與行政區聚合 fill layer。
   - 適合 demo，因為文化近用與空間分布直接相關。

2. **藝文活動可近性與票價結構**
   - 臺北文化快遞可直接使用活動經緯度。
   - 新北資料若缺座標，先做行政區層級統計，不強行精準點位。

街頭藝人與文化政策支持以 chart 為主，不建議第一版強行地圖化。

## 風險與限制

- 臺北與新北資料欄位不完全一致，雙北比較必須先定義共同欄位。
- 臺北文化快遞含票價與座標，新北藝文活動欄位較簡，活動可近性比較需標示資料缺口。
- 部分文化資產、公共藝術與展演場地資料只有地址，需地址清理或行政區聚合。
- 街頭藝人資料可能包含姓名、電話、Email 等個資欄位；dashboard 與 AI 回答應使用彙整統計，避免不必要揭露。
- 補助案與團體登記地址不等於實際服務範圍，不應直接解讀為文化服務受益地。
- 新北藝文展演活動統計目前搜尋到 staging 資料頁，實作前需再確認正式資料頁是否可用。
- AI Chat 應查詢內部資料表，不應在使用者提問時即時打外部 API。
- AI 回答必須附帶資料來源、更新時間與限制，避免把不完整資料解讀成完整事實。

## 推薦 MVP

第一版先完成：

1. 文化資源與公共藝術分布地圖，含行政區聚合與 point layer。
2. 藝文活動可近性與票價結構，先支援活動類型、期間、免費/付費比例與行政區分布。
3. 街頭藝人與演藝團體多元參與，先做類型與性別統計。
4. 文化政策支持與地方文化組織，先做臺北補助案、新北演藝團體/基金會與雙北組織密度比較。
5. AI Chat 支援「文化資源搜尋」、「雙北比較」、「行政區排行」、「活動推薦」、「資料限制說明」五類問題。
