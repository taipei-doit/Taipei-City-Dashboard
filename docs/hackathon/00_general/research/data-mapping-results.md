# Data Source Mapping & RID Registry

This document serves as the "source of truth" for the Taipei City Dashboard data integrations, replacing legacy/broken links identified in early verification pulses.

## 🔴 Critical Real-Time Tracks

| Indicator | Agency | RID / Endpoint | Format | Status |
| :--- | :--- | :--- | :--- | :--- |
| **淹水感測 (Flood)** | 台北水利處 | `192f155c-15ba-4122-863a-23743f553a1c` | JSON/API | Verified (System active) |
| **景點人潮 (Crowd)** | 台北觀傳局 | `https://travel.taipei/stream/alert-of-crowds/json` | JSON | **Blocked** (CF Protection) |
| **全國急診 (Live ER)** | 衛福部 | `125195` (data.gov.tw) | JSON | Verified |
| **台北 AED** | 台北衛生局 | `438c61ad-24f6-4e54-a1cc-e2cfe0e7051e` | JSON | Verified (Dataset: cd050577) |

> [!CAUTION]
> **Crowd Lighting API**: Direct access is currently blocked by Cloudflare bot protection. For the hackathon demo, either use a backend proxy with header spoofing or utilize the `mock_crowd_data.json` localized in `Taipei-City-Dashboard/data/`.

## 🟡 Socio-Economic & Vulnerability Indices

### 1. Taipei City Population (Age Stats)
- **Dataset ID**: `64c8a3a0-3b9a-4f49-a13a-fb1eb2ffa4b1`
- **Corrected Download**: `https://data.taipei/api/dataset/64c8a3a0-3b9a-4f49-a13a-fb1eb2ffa4b1/resource/edf9a589-7095-4f18-995f-f8657c0d8c1a/download`
- **Fields**: `區域別`, `性別`, `總計`, `65歲以上數量` (derivable from single-age columns).

### 2. New Taipei Population (Age Stats)
- **Dataset ID**: `8308AB58-62D1-424E-8314-24B65B7AB492`
- **Schema Mapping**:
    - `field1`: 行政區 (District)
    - `percent2`: **總人口 (Total Population)**
    - `percent28`: **65歲以上人口數 (Vulnerable Age Count)**
    - `percent33`: **老化指數 (Aging Index)**

## 🟢 Resilience & Infrastructure

| Layer | Agency | RID / URL |
| :--- | :--- | :--- |
| **台北避難處所** | 台北教育局 | `aaf97773-3631-40e2-b3cc-da87bf2ce1d5` (RID: `4c92dbd4`) |
| **新北避難處所** | 新北社會局 | `25E439AB-49E7-4E5E-85CE-A25C13FD2770` |

---
**Verification Date**: 2026-04-15
**Sign-off**: AI Architect (Antigravity)
