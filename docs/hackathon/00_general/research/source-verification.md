# Official Source Verification

This file records which sources have actually been checked and what they give us.

## Status legend

- **Verified** = the source page exists, has a usable format, and gives us enough metadata to reason about joins.
- **Useful but incomplete** = the source exists, but we still need a deeper pull or a join test.
- **Parked** = not useful for the current primary topic.

## Verified sources for the current primary topic

| Source | Status | Evidence | Likely role in the plan | Current gap |
|---|---|---|---|---|
| [`臺北市氣候變遷調適執行方案` / Taipei climate adaptation pages](https://sdg.gov.taipei/page/cn_area2/53) | Verified | The page explicitly says Taipei’s盆地地形 and urban concrete density create a heat-island effect and mentions adaptation policy. | Policy context, judge framing, why now | Not a direct data table, so it supports the story but not the map layer by itself. |
| [`臺北市扶養比及老化指數`](https://data.taipei/dataset/detail?id=aafb15dc-5508-4091-bd48-a708e60f6698) | Useful but incomplete | Taipei data portal exposes CSV download and annual city-level aging/dependency fields. | Citywide context / sanity check | It does not look like the primary district-level join source. Keep it as context, not the main vulnerability layer. |
| [`臺北市各區人口數按年齡分`](https://data.taipei/dataset/detail?id=64c8a3a0-3b9a-4f49-a13a-fb1eb2ffa4b1) | Verified | Taipei data portal exposes monthly CSV downloads and district-level age fields. | Primary vulnerability proxy | Need to decide whether we use full age bands or a reduced index. |
| [`臺北市可供避難收容處所一覽表`](https://data.taipei/dataset/detail?id=aaf97773-3631-40e2-b3cc-da87bf2ce1d5) | Verified | Taipei data portal exposes CSV download and fields for address, district, village, capacity, and hazard suitability. | Shelter/resource layer | Need to verify which records are spatially usable without cleanup. |
| [`臺北市防空疏散避難設施資料集`](https://data.taipei/dataset/detail?id=70a6216e-3730-4d1d-b334-62fca2dd71cd) | Verified | Taipei data portal exposes a current CSV with address, coordinates, capacity, and management metadata. | Fallback shelter-like layer | This is useful, but we should not mix it with the shelter list unless the story needs it. |
| [`臺北市涼適點`](https://data.taipei/dataset/detail?id=a98a3e0e-a36f-43fa-82f8-b09a3011a47a) | Verified | Taipei data portal exposes CSV with indoor/outdoor location, coordinates, opening hours, cooling features, and accessibility features. | Cooling-resource layer | This is the strongest direct “heat relief” resource source so far, but we still need a join test. |
| [`臺北市銀髮族服務_社區照顧關懷據點`](https://data.taipei/dataset/detail?id=d082dc87-d3fd-479d-89c6-745ff1be955a) | Verified | Taipei data portal exposes CSV with name and address. | Elder-care backup, access proxy | No coordinates shown in the snippet, so geocoding may be needed. |
| [`現住人口之年齡分配`](https://data.ntpc.gov.tw/datasets/8308AB58-62D1-424E-8314-24B65B7AB492) | Verified | New Taipei portal exposes CSV/JSON/XML, yearly updates, district-level age bands, dependency ratios, and aging index. | Vulnerability proxy | Need to confirm the exact district field values we can join against Taipei. |
| [`新北市避難收容處所一覽表`](https://data.ntpc.gov.tw/datasets/25E439AB-49E7-4E5E-85CE-A25C13FD2770) | Verified | New Taipei portal exposes CSV/JSON/XML and fields for district, village, address, capacity, and hazard suitability. | Shelter/resource layer | Good candidate, but we still need a spatial normalization rule. |
| [`推行社區發展工作成果`](https://staging.data.ntpc.gov.tw/datasets/a584c4a7-bacc-4f39-99ee-fa12f95225e1) | Useful but incomplete | New Taipei portal exposes annual district-level counts, including `辦理社區照顧關懷據點_處_`. | Access-resource proxy | Useful as a district-level proxy, but not a direct point map, and the URL is on a staging host. |
| [`氣象資料開放平台`](https://opendata.cwa.gov.tw/index) | Verified | CWA open data platform exists and exposes observation/climate products plus docs. | Heat exposure context | We still need to pick the exact observation or warning product for the MVP. |
| [`高溫資訊`](https://www.cwa.gov.tw/V8/C/P/Warning/W29.html?T=202506141725) | Verified | CWA product page states the warning thresholds and mentions county/city and township-level handling. | Heat-risk trigger / explanation | This is a good trigger source, but not yet the final map layer. |
| [`觀測要素項目及產品型式對應表`](https://www.cwa.gov.tw/Data/data_catalog/obs_element_item_table.pdf) | Verified | The catalog shows temperature is available in hourly observation products. | Heat exposure layer candidate | Need to choose the concrete dataset code and test the fetch path. |

## What this means

We now have enough official evidence to keep the **heat island + vulnerable groups** topic alive.

What we do **not** have yet is the whole chain:

1. exact heat exposure layer,
2. exact join rule,
3. exact PR wedge mapping to the dashboard repo,
4. sample evidence set for the demo.

So the topic is **promising**, not locked.

## Recommended next verification pass

### Pass 1: join test
Take one Taipei district and one New Taipei district, and test:
- age proxy,
- shelter resource,
- cooling-resource or care-point proxy,
- and one heat trigger source.

### Pass 2: grain check
Verify whether the data lives at:
- district,
- village,
- facility,
- or time-series level.

### Pass 3: fallback trigger
If the heat-layer join fails, pivot to:
- `災害避難 + 物資收容調度`

If the shelter and hazard layers also fail, pause and pick a different topic. Do not brute-force it.
