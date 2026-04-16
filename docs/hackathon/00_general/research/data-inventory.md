# Data Inventory

## Purpose
This file tracks the official/open datasets needed to make the primary topic real.

## Evidence-backed candidate sources already found

### Taipei
- `臺北市永續發展資訊網` heat island / climate adaptation context: `sdg.gov.taipei`
- `臺北市扶養比及老化指數`: `data.taipei/dataset/detail?id=aafb15dc-5508-4091-bd48-a708e60f6698`
- `臺北市各區人口數按年齡分`: `data.taipei/dataset/detail?id=64c8a3a0-3b9a-4f49-a13a-fb1eb2ffa4b1`
- `臺北市可供避難收容處所一覽表`: `data.taipei/dataset/detail?id=aaf97773-3631-40e2-b3cc-da87bf2ce1d5`
- `臺北市銀髮族服務_社區照顧關懷據點`: `data.taipei/dataset/detail?id=d082dc87-d3fd-479d-89c6-745ff1be955a`
- `臺北市社區血壓量測網絡地圖一覽表`: `data.taipei/dataset/detail?id=0684472f-406f-4ad2-9eee-76fc47acccf7`
- `臺北市公眾區免費無線上網熱點資料(新版)`: `data.taipei/dataset/detail?id=6aa6532d-652f-4c1b-814a-4646b75407af`

### New Taipei
- `現住人口之年齡分配`: `data.ntpc.gov.tw/datasets/8308AB58-62D1-424E-8314-24B65B7AB492`
- `新北市避難收容處所一覽表`: `data.ntpc.gov.tw/datasets/25E439AB-49E7-4E5E-85CE-A25C13FD2770`
- `遭受災害救助情形`: `data.ntpc.gov.tw/datasets/05e9a748-13c6-4fd0-babb-ab48024e7f49`

## What must be proven
For every source, verify:

- it exists,
- it is official or openly published,
- it has a usable format,
- it can join with at least one other dataset,
- it does not force the dashboard into a misleading granularity.

## Inventory template

| Category | Candidate source | Format | Join key / spatial strategy | Update cadence | Notes |
|---|---|---|---|---|---|
| Heat exposure | official climate / meteorological source | API / CSV / GeoJSON | district / grid / station | daily or event-based | verify scope and licensing |
| Population vulnerability | official population / age structure source | CSV / table | district / village | monthly / annual | use proxy carefully |
| Cooling / shelter resources | official public facility source | CSV / GeoJSON | address / facility / district | periodic | check whether location data is precise enough |
| Green / built environment | official land-use / green coverage source | GIS / CSV | district / grid | periodic | support explanation, not diagnosis |
| Emergency / response resources | official social welfare / disaster source | CSV / table | district / facility | periodic | define which action it supports |

## Primary topic likely join path

For **Heat island + vulnerable groups**, the first-pass join path is likely:

- geography: district level or a compatible spatial layer,
- vulnerability: age structure / aging index,
- resources: shelters, social care points, network / access proxies,
- context: climate / heat island narrative from official policy pages,
- optional transport/access proxy: facility location and hotspot coverage.

If that path does not hold, do not force it.

## Joinability checklist

- [ ] One common geographic layer exists
- [ ] One common time layer exists or is clearly optional
- [ ] Facility records can be geocoded or matched safely
- [ ] Proxy variables are clearly labeled as proxies
- [ ] No source is used at a finer granularity than it can support

## Known failure modes

- PDF-only source with no table extraction path
- district / village / station mismatch
- annual demographic data mixed with near-real-time hazard data
- incompatible licensing or reuse constraints
- confusing proxy variables with direct measurements
