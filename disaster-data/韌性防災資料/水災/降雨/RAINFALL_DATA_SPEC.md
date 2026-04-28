雙北雨量監測資料規格書
一、 欄位定義表
| 欄位名稱    | 類型     | 說明                           |
| ------------ | ------ | ---------------------------- |
| station_id   | String | 測站唯一編碼 (如: 466900)           |
| station_name | String | 測站名稱 (如: 淡水)                 |
| city         | String | 縣市名稱 (臺北市/新北市)               |
| district     | String | 行政區名稱 (如: 淡水區)               |
| lat / lon    | Float  | 緯度 / 經度 (WGS84)              |
| update_time  | String | 資料觀測時間，顯示「最後更新時間」。           |
| rain_daily   | Float  | 本日累積雨量 (mm)，當日 00:00 起算之累積量。 |
| rain_1hr     | Float  | 時雨量 (1hr)，預警核心指標，判斷當前雨勢。     |
| rain_10min   | Float  | 10 分鐘雨量 (mm)，判定瞬間降雨強度。       |
| rain_24hr    | Float  | 24 小時累積雨量，判定大雨/豪雨等級之標準。      |

二、補充 
1. 雨量分級定義參考檔案：https://share.google/k9X10mS9YZ4Nkn2ZG
2. 更新時間:10分鐘1次
3. 資料來原:雨量觀測站-雨量資料https://opendata.cwa.gov.tw/dataset/forecast/O-A0002-001


