

取得 TDX 平台 token（需自行申請帳號）。可在 `/dag/utils/transform_address.py` 查看相關程式碼。

> **w01**
> 務必確認你已經查看[下載並設定專案](/data-end/project-setup)章節並設置完成。

> **w02**
> 若開發者在 Airflow 環境想單獨測試以下程式碼，需先執行以下程式碼取得環境設定。
> ``` python
> from airflow import DAG
> ```

> **w03**
> 若開發者需要在非 Airflow 的環境測試以下程式碼，需添加以下幾行程式，以確保將本專案的路徑加入環境變數，從而能找到 `utils` 與 `settings` 等資料夾：
> ``` python
> import os
> import sys
>
> dags_path = os.path.join(os.getcwd(), 'dags') 
> sys.path.append(dags_path)
> ```

## 函式說明

### class TDXAuth

原始碼可以在 `/dags/utils/auth_tdx.py` 找到。此程式用於取得 TDX 的 token。每次取得 token 後會儲存為 `token.pickle` 檔案，並在後續程序中重複使用該 token 直到過期，然後再重新取得並儲存。
TDX 的 token 需要驗證才能取得，務必確認你的 `TDX_CLIENT_ID` 與 `TDX_CLIENT_SECRET` 已添加至 Airflow Variables。

使用範例如下：

```python
# Get Taipei YouBike stations from TDX
import requests
import pandas as pd
from utils.auth_tdx import TDXAuth

TPE_URL = r"https://tdx.transportdata.tw/api/basic/v2/Bike/Station/City/Taipei?%24format=JSON"

tdx = TDXAuth()
token = tdx.get_token()
# get data
headers = {"authorization": f"Bearer {token}"}
tpe_response = requests.get(TPE_URL, headers=headers, timeout=60)
tpe_res_json = tpe_response.json()
tpe_data = pd.DataFrame(tpe_res_json)
print(tpe_data)
```

```
>>> print(tpe_data.iloc[0])
StationUID                                              TPE500101001
StationID                                                  500101001
AuthorityID                                                      TPE
StationName        {'Zh_tw': 'YouBike2.0_捷運科技大樓站', 'En': 'YouBike...
StationPosition    {'PositionLon': 121.5436, 'PositionLat': 25.02...
StationAddress     {'Zh_tw': '復興南路二段235號前', 'En': 'No.235, Sec. 2...
BikesCapacity                                                     28
ServiceType                                                        2
SrcUpdateTime                              2024-05-06T20:43:18+08:00
UpdateTime                                 2024-05-06T20:43:26+08:00
Name: 0, dtype: object
```
