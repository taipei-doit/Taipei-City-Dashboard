雙北區域人口統計資料規格書

一、 欄位定義表 (Data Schema)
| 欄位名稱 (Key)   | 類型     | 說明                 |
| ------------ | ------ | ------------------ |
| city         | String | 縣市名稱 (臺北市/新北市)     |
| district     | String | 行政區名稱(如中山區)           |
| households   | Integer| 戶數                 |
| male         | Integer| 男性人口             |
| female       | Integer| 女性人口             |
| total_population | Integer| 合計人口             |

二、 補充
1. 更新時間:一個月更新一次
2. 資料來源:
    - 臺北市各行政區最新月份人口數及戶數：https://data.taipei/dataset/detail?id=6a1dbb4e-e99c-4e67-ab09-f6d83852dc99
    - 新北市各區人數統計表：https://data.ntpc.gov.tw/datasets/292443d2-faef-452c-96cd-33053e7369b6