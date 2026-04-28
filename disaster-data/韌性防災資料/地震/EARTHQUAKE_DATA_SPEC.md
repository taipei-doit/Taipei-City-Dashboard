雙北地震觀測資料規格書

一、 欄位定義表 (Data Schema)
| 欄位名稱 (Key)   | 類型     | 說明                 |
| ------------ | ------ | ------------------ |
| update_time  | String | 地震發生原始時間 (ISO8601) |
| city         | String | 縣市名稱 (臺北市/新北市)     |
| station_name | String | 測站名稱 (如: 五分山)      |
| intensity    | String | 地震震度 (如: 2級, 3級)   |
| lat          | Float  | 緯度 (WGS84)         |
| lon          | Float  | 經度 (WGS84)         |
| pga_ns       | Float  | 地動加速度 (NS方向)       |

二、 補充
1. 更新時間:不定期
2. 資料來源:https://opendata.cwa.gov.tw/dataset/earthquake/E-A0015-001
