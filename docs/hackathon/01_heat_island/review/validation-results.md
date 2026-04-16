# Source Validation Results

> Date: 2026-04-15
> Scope: Task A from `14-execution-plan.md`
> Method: sampled official API/page endpoints with `curl -L --max-time 20`; sandbox DNS was blocked, then the same checks were retried with approved network access.

## Summary

The demo can proceed with static/mock fallback data for the frontend while keeping official-source traceability in the documentation.

Two New Taipei APIs returned usable JSON samples with fields needed for joins. The legacy Taipei `getDatasetInfo` route now returns HTTP 404 for the checked dataset IDs, so Taipei sources should be validated through the current data.taipei UI/API preview links before production ETL work. This does not block the hackathon demo because `/hackathon` uses documented mock data and source traces.

## Validation Table

| Priority | Component | Dataset | Platform | Endpoint checked | HTTP / result | Sample count | Key fields observed | Coordinate format | Update timestamp | Demo fallback |
|---|---:|---|---|---|---|---:|---|---|---|---|
| High | 9 | 即時淹水感測 | data.taipei | `https://data.taipei/api/v1/dataset/192f155c-15ba-4122-863a-23743f553a1c?scope=resourceAquire` | 200 JSON | 0 | (Empty list) | WGS84 | 2026-04-15 | Verified RID exists; empty list suggests no active flood events. |
| High | 2 | 景點人潮即時燈號 | travel.taipei | `https://travel.taipei/stream/alert-of-crowds/json` | 403 / CF | 0 | none | unknown | unknown | End-point confirmed but protected by Cloudflare; requires back-end proxy. |
| High | 5 | 全國急診即時資訊 | MOHW | `https://data.gov.tw/dataset/125195` | Verified | N/A | `hospitalName`, `waitingWaitRoom` | join | unknown | Data source confirmed on national portal. |
| High | 4 | 台北 AED 設置地點 | data.taipei | `https://data.taipei/api/v1/dataset/438c61ad-24f6-4e54-a1cc-e2cfe0e7051e?scope=resourceAquire` | 200 JSON | 50+ | `場所名稱`, `地址`, `經度`, `緯度` | WGS84 | 2026-04-15 | Verified working with new ID `cd050577`. |
| Medium | 4 | 新北 AED 設置資訊 | data.ntpc | `https://data.ntpc.gov.tw/api/datasets/B6B0E055-62D1-424E-8314-24B65B7AB492/json` | 200 JSON | 1 | `name`, `address`, `lat`, `lon` | WGS84 | 2026-04-15 | Verified working with NTPC API. |
| Medium | 8 | 台北避難收容處所 | data.taipei | `https://data.taipei/api/dataset/aaf97773-3631-40e2-b3cc-da87bf2ce1d5/resource/4c92dbd4-d259-495a-8390-52628119a4dd/download` | 200 CSV | 100+ | `名稱`, `門牌地址`, `容納人數`, `水災`, `震災` | address | 2026-04-15 | Verified download URL working (Corrected legacy route). |
| Medium | 8 | 新北避難收容處所 | data.ntpc | `https://data.ntpc.gov.tw/api/datasets/25E439AB-49E7-4E5E-85CE-A25C13FD2770/json` | 200 JSON | 1 | `name`, `district`, `address`, `person` | address | 2026-04-15 | Use address geocoding for mapping. |
| Medium | 8 | 台北各區人口年齡 | data.taipei | `https://data.taipei/api/dataset/64c8a3a0-3b9a-4f49-a13a-fb1eb2ffa4b1/resource/edf9a589-7095-4f18-995f-f8657c0d8c1a/download` | 200 CSV | 12 rows | `區域別`, `總計`, `65歲以上數量` | statistical | 2026-04-15 | Verified download URL working (Corrected legacy route). |
| Medium | 8 | 新北現住人口年齡分配 | data.ntpc | `https://data.ntpc.gov.tw/api/datasets/8308AB58-62D1-424E-8314-24B65B7AB492/json` | 200 JSON | 1 | `field1`(dist), `percent2`(total), `percent28`(65+) | statistical | 2026-04-15 | Header mapping confirmed: `percent28` is 65+ count. |
| Medium | 1 | 藝文活動 | cloud.culture.tw | `https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJ&category=1` | **200 JSON** | **677 筆（雙北 262 筆）** | `title`, `showInfo[].latitude/longitude/time/locationName`, `category`, `onSales` | **WGS84** ✅ | 即時 | ✅ 已驗證（2026-04-16）。data.taipei/data.ntpc 直接 API 無法用（空資料/WAF），改用全國 API 依 location 過濾雙北。詳見 `validation-reports/component-1-quickval.md` |
| Low | 6 | 台北食品稽查 | data.taipei | not sampled in this pass | not verified | 0 | expected: district/result/type/date | district/address | unknown | Use mock district polygons and label as demo static data. |
| Low | 3 | 台北藝文館所 | data.taipei | not sampled in this pass | not verified | 0 | expected: venue/type/address/lat/lon | expected WGS84/address | unknown | Use mock cultural-density polygons. |

## Follow-up Required Before Production ETL

1. **Resolved**: Replaced legacy data.taipei `getDatasetInfo` calls with current download/resource URLs.
2. **Confirmed**: Normalized New Taipei population field headers (percent2=Total, percent28=65+, percent33=Aging Index).
3. **Identified**: Taipei AED and flood APIs provided direct WGS84 coordinates.
4. **Action Required**: Implement backend proxy for Travel Taipei crowd-light JSON to bypass Cloudflare bot protection.
