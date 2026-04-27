雙北河川即時水位資料規格書 
一、 欄位定義表 
| 欄位名稱     | 類型     | 說明                     |
| ------------- | ------ | ---------------------- |
| station_id    | String | 測站唯一編碼 (如: 1140H029)   |
| station_name  | String | 觀測站名稱 (如: 台北橋)         |
| address       | String | 行政區位置 / 詳細地址           |
| water_level   | Float  | 目前水位 (公尺)              |
| update_time   | String | 資料更新時間 (ISO8601)       |
| alert_level_1 | Float  | 一級警戒水位，0.0 代表該站無此預警功能。 |
| alert_level_2 | Float  | 二級警戒水位，0.0 代表該站無此預警功能。 |
| alert_level_3 | Float  | 三級警戒水位，0.0 代表該站無此預警功能。 |
| lat           | Float  | 緯度 (WGS84)             |
| lon           | Float  | 經度 (WGS84)             |

二、 核心業務邏輯：
1. 由於部分站點不具備預警功能，已將其 `alert_level` 統一補為 `0.0`。

三、 補充
1. 更新時間:10分鐘1次
2. 資料來源:水利署https://opendata.wra.gov.tw/openapi/swagger/index.html#/%E6%B2%B3%E5%B7%9D%E8%88%87%E6%8E%92%E6%B0%B4/get_api_v2_73c4c3de_4045_4765_abeb_89f9f9cd5ff0
    - 即時水位資料 
    - 河川水位測站站況