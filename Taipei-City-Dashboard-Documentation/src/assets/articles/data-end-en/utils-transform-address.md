

用於清洗、標準化、分解地址，建議適用於台北市地址。其中有部分為子函式，將不會說明子函式。可在 `/dag/utils/transform_address.py` 查看相關程式碼。

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

### -函式 clean_data(addr)

清洗地址，包含全形轉半形、去除括弧、去除標點符號、替換常見錯字、處理部分難字、段的數字改為國字數字等...

```python
import pandas as pd
from utils.transform_address import clean_data

addres = pd.Series(['台北市信義區3民路四段３00號-1(3室)', '信義路-８號之之5樓'])
ca = clean_data(addres)
print(ca)
```

```
>>> print(ca)
0    台北市信義區三民路四段300號之1
1             信義路之8號5樓
dtype: object
```

### -函式 main_process(addr_cleaned)

辨識並切分地址，同時提供程式判斷信心等級。

### -函式 save_data(addr, addr_cleaned, standard_addr_list)

與 `main_process` 配套使用，將結果轉換為 pd.DataFrame。

```python
import pandas as pd
from utils.transform_address import (
    clean_data,
    main_process,
    save_data
)

addres = pd.Series(['台北市信義區3民路四段３00號-1(3室)', '信義路-８號之之5樓'])
addr_cleaned = clean_data(addres)
standard_addr_list = main_process(addr_cleaned)
result, output = save_data(addres, addr_cleaned, standard_addr_list)
print(result.iloc[0])
```

```
>>> print(result.iloc[0])
status                                                 not null
conf_level                                              perfect
postcode
city                                                        台北市
dist                                                        信義區
vil
nebd
road                                                      三民路四段
lane
alley
sub_alley
num                                                        300號
floor
room                                                         之1
other                                               ,,,,,,,,,,,
output                                          台北市信義區三民路四段300號
log           data row 0:\npostcode seg fail: Can't find pat...
raw                                       台北市信義區3民路四段３00號-1(3室)
cleaned                                       台北市信義區三民路四段300號之1
Name: 0, dtype: object
```
