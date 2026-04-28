雙北醫療量能資料規格書 

一、 欄位定義表 
| 欄位名稱      | 類型      | 說明                   |
| -------------- | ------- | -------------------- |
| update_time    | String  | API 系統更新時間           |
| city           | String  | 所屬縣市 (臺北市/新北市)       |
| hospital_name  | String  | 醫院名稱                 |
| is_full_119    | Integer | 119 滿床通報 (1:是 / 0:否) |
| wait_see       | Integer | 等待看診人數               |
| wait_push_bed  | Integer | 等待推床人數               |
| wait_admission | Integer | 等待住院人數               |
| wait_icu       | Integer | 等待 ICU (重症) 人數       |

二、補充
1. 更新時間:每 15 分鐘更新一次 
2. 資料來源:https://github.com/KJT125/Nhi-er-open-data