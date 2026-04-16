TL;DR：不要再把「AI 決策卡片」當首頁。最簡單、最直觀、最像民眾儀表板的做法，是把首頁改成 **「今天這區適不適合出門／去哪裡比較好」**，用穩定資料先做出可用底盤；官員版災難劇本保留成第二頁 demo 模式，不要混在同一個首頁。

你現在這個畫面最大問題，不是技術，而是語言層級錯了。

目前首頁在講：

* AI 決策卡片
* 風險 / 副作用 / 信心
* 採納 / 替代方案
* 劇本標籤

這些都是官員、指揮、內部決策語言。
民眾首頁不會想看「副作用視覺化」，民眾只想知道：

* 我這區現在狀況如何
* 我該不該出門
* 要去哪裡比較好
* 為什麼

官方規則確實要求你們作品不能只停在資料展示，還要有 AI、決策卡片與副作用視覺化；但同時，台北資料平台對城市儀表板的官方定位也明寫，這套系統已經從內部市政決策延伸成對外提供市民服務、讓市民掌握生活周遭資訊的工具。也就是說，你不是只能做官員版，也不是只能做民眾版；正解是 **同底盤、雙視角**。 ([台北市資料大平臺][1])

所以工程上最乾淨的版本是這樣。

一、先改產品定義

不要再把整個專案定義成「防災 AI 決策台首頁」。
改成兩層：

**首頁：民眾版儀表板**

* 核心問題：今天這區適不適合出門？
* 核心互動：看地圖、看分數、看原因、看建議去處
* 核心語言：生活判讀，不是指揮語言

**第二頁：評審 / 官員劇本模式**

* 保留 AI 決策卡片
* 保留副作用 hover 高亮
* 保留劇本切換
* 只在 demo 時展示

這樣同時滿足：

* 「儀表板」核心
* 民眾可理解
* 評審要求的 AI / side effect
* 工程可拆分成 PR wedge 

二、V1 不要選災難當民眾首頁主題

不是因為防災不能做，而是你目前關鍵資料正好最不穩：

* 你自己的執行計畫已經標出即時淹水、景點人潮燈號、急診即時資訊都是高風險待驗證，且 data.taipei 的舊 `getDatasetInfo` 路由已 404。
* 反過來，文化部活動、環境部 AQI、中央氣象署開放資料這三條，目前都有公開資料頁或 API 使用說明；環境部還直接公開了 API URL 格式。([opendata.culture.tw][2])

所以最穩的民眾版首頁，不是「災害劇本」，而是：

**C3：走出門指數**

* 天氣
* AQI
* UV
* 降雨
* 可加上附近活動

這個主題的好處是：

* 問題單一，民眾一秒懂
* 是真正的 dashboard，不是劇情播放器
* AI 可以只做一句話摘要，不必當主角
* 資料源比防災穩定得多  ([環境資料開放平臺][3])

三、首頁畫面直接重做成這個結構

不要左邊 10 個組件列表，也不要首頁先進劇本模式。

改成四塊：

**1. 頂部一條核心卡**

* 文案：`板橋區｜現在適合出門：72 / 100`
* 子文案：`空氣普通、午後降雨機率高、晚間有 12 場活動`

**2. 中央主地圖**

* 不要用複雜點位先轟炸
* 直接用雙北行政區 choropleth
* 綠 / 黃 / 紅 三色
* 點區域才展開細節

**3. 右側三張理由卡**

* 天氣
* 空氣品質
* 今日活動 / 外出建議

**4. 底部詳細區**

* 12 小時趨勢線
* 附近活動清單
* 這區為什麼是 72 分的分數拆解

這樣才是「儀表板」。
你現在那種「決策卡片 + 採納按鈕 + 副作用圖層」比較像戰情系統子頁，不像民眾首頁。

四、資料層只做一個最小閉環

不要再同時打 10 個組件。
V1 只做這 4 張標準表：

**raw_sources**

* source_name
* fetched_at
* payload_json

**district_snapshot**

* city
* district
* weather_score
* aqi_score
* uv_score
* rain_score
* event_score
* total_score
* last_updated

**district_reason**

* city
* district
* factor
* label
* value
* severity
* explanation

**place_events**

* city
* district
* title
* category
* start_time
* lat
* lon
* source_url

這很符合你們規則裡強調的 schema / widget / adapter 可拆分思路，也比一開始就把 tool registry、決策引擎、MATSim、MiroFish 全塞進主路徑穩得多。

五、先用這些資料，不要碰現在最卡的

V1 建議資料源：

**直接用**

* 中央氣象署：天氣、降雨、UV 開放資料平台與 API 文件可用，需授權碼。([opendata.cwa.gov.tw][4])
* 環境部：AQI 有正式資料集與 API URL 格式說明。([環境資料開放平臺][5])
* 文化部：藝文活動 JSON / OAS 文件可用。([opendata.culture.tw][2])

**第二階段再加**

* TDX 交通資料，要申請 API Key，資料豐富但 join 成本高。([交通數據平台][6])
* data.taipei / data.ntpc 的區域設施與生活資料

**先不要當主路徑**

* 即時淹水
* 景點人潮燈號
* 急診即時壅塞

原因不是永遠不能做，而是你現在最需要的是先把首頁做成，而不是繼續被資料驗證拖死。你自己的驗證計畫也已經把這幾項列為 Critical 未解。

六、data.taipei 的正確處理方式

你現在的判斷方向是對的：不要再打舊的 `getDatasetInfo`。

目前從官方頁面能確認的是：

* 資料集詳細頁仍提供「下載 / API / 預覽」入口，例如台北避難收容所與台北各區人口數按年齡分都還在。([台北市資料大平臺][7])
* 台北 AED 資料集目前存在，且欄位已含緯度、經度、場所分類等，更新頻率為每月。([台北市資料大平臺][8])
* 公開索引中可看到新的下載形式已是 `/api/dataset/{dataset-id}/resource/{resource-id}/download` 這種路徑，而不是你現在用的 legacy route。([台北市資料大平臺][9])

所以工程動作不是「繼續猜 endpoint」，而是：

1. 以資料集詳細頁為 source of truth
2. 先人工抄出 dataset_id / resource_id
3. 寫一支小型 registry 檔統一管理
4. 每個資料源先落地成 raw file 或 cache table
5. 再做 normalize

新北這邊反而比較乾淨，官方已明確提供 OpenAPI 與資料集頁，例如避難收容所與 AED 都有 JSON / CSV / XML / OpenAPI 入口。([data.ntpc.gov.tw][10])

七、AI 在 V1 的定位要縮到最小

不要一開始就做完整 tool-calling 決策系統上首頁。

V1 的 AI 只做一件事：

**把 deterministic 結果翻譯成人話**

例如：

* `板橋今天 72 分，因午後降雨機率升高，不建議長時間戶外活動；若要出門，晚上室內展覽比河濱活動更穩。`

這就夠了。

也就是：

* 分數與顏色：規則引擎算
* 地圖顯示：前端 deterministic
* AI：只負責摘要與說明

這也比較符合你們規則寫的 AI 行為邊界：AI 可以做跨城市數據摘要、情境對比、話術草稿與風險分析，但不能靠黑箱硬預測撐整個系統。

八、最小工程清單

你現在就該做這 8 件事：

1. 把首頁主題改成「走出門指數」
2. 拿掉首頁的採納 / 替代方案 / 信心值 / 劇本標籤
3. 後端先只接 3 個來源：CWA、MOENV、文化部
4. 建一支 `source_registry.yaml` 管 dataset_id、resource_id、refresh interval
5. 每 10–30 分鐘做一次 ingestion + cache
6. 寫一個 deterministic `score_engine`
7. 前端只保留一張地圖、三張卡、一個 detail drawer
8. AI 僅保留 `explain_score()` 一個入口

九、災難劇本可不可以給民眾用

可以，但只能給民眾看「結果層」，不能直接給「指揮層」。

民眾版災難頁只該保留：

* 你所在區域風險
* 建議避開區域
* 最近避難點 / 室內點
* 一句話建議
* 下次更新時間

不要給民眾看：

* 採納 / 延後 / 替代
* 信心值
* 副作用壓力轉移百分比
* 指揮決策優先序

所以正確做法不是刪掉官員版，而是：

**首頁做民眾版儀表板**
**另保留 `/scenario` 或 `/ops` 頁做評審 demo 的官員劇本模式**

這樣你既符合賽規，又不會把首頁做成一個難懂的戰情系統。

最後定調一句：

**先做一個民眾看得懂、資料拿得到、AI 只做翻譯的儀表板首頁；再把官員版災難劇本藏在第二頁，作為評審展示模式。**

[1]: https://data.taipei/ "臺北市資料大平臺"
[2]: https://opendata.culture.tw/frontsite/openData/detail?datasetId=302&utm_source=chatgpt.com "藝文活動-所有類別 - :::文化資料開放服務網:::"
[3]: https://data.moenv.gov.tw/paradigm "API 使用說明 | 環境部環境資料開放平臺"
[4]: https://opendata.cwa.gov.tw/?utm_source=chatgpt.com "中央氣象署-開放資料平臺"
[5]: https://data.moenv.gov.tw/dataset/detail/aqx_p_432?utm_source=chatgpt.com "空氣品質指標(AQI) - 環境資料開放平臺"
[6]: https://tdx.transportdata.tw/maas?utm_source=chatgpt.com "MaaS交通行動服務開放API - | TDX 運輸資料流通服務"
[7]: https://data.taipei/dataset/detail?id=aaf97773-3631-40e2-b3cc-da87bf2ce1d5 "臺北市資料大平臺 ｜ 臺北市可供避難收容處所一覽表"
[8]: https://data.taipei/dataset/detail?id=cd050577-115f-4299-b37a-012ff490a632&utm_source=chatgpt.com "臺北市AED自動體外心臟去顫器設置地點"
[9]: https://data.taipei/api/dataset/cd050577-115f-4299-b37a-012ff490a632/resource/438c61ad-24f6-4e54-a1cc-e2cfe0e7051e/download?utm_source=chatgpt.com "https://data.taipei/api/dataset/cd050577-115f-4299..."
[10]: https://data.ntpc.gov.tw/datasets/25e439ab-49e7-4e5e-85ce-a25c13fd2770?utm_source=chatgpt.com "新北市避難收容處所一覽表"
