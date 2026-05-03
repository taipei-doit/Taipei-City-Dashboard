

包含處理民國年、標準化時間與時區、去除時間中有上下午中文的函式。其中有部分為子函式，將不會說明子函式。可在 `/dag/utils/transform_time.py` 查看相關程式碼。

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

### -函式 convert_str_to_time_format(time_column)

擴充自 `pd.to_datetime`，除了讓輸出包含 time zone 以外，還可以處理民國年，並增加輸出彈性。多個範例如下：

```python
import pandas as pd
from utils.transform_time import convert_str_to_time_format

time_column = pd.Series(['2022/12/31 00:12:21', '2022/1/31 01:02:03'])
convert_str_to_time_format(time_column)
# Output:
# 0   2022-12-31 00:12:21+08:00
# 1   2022-01-31 01:02:03+08:00
# dtype: datetime64[ns, Asia/Taipei]

time_column = pd.Series(['110/12/31 00:12:21', '111/1/31 01:02:03'])
convert_str_to_time_format(time_column, from_format='%TY/%m/%d %H:%M:%S')
# Output:
# 0   2021-12-31 00:12:21+08:00
# 1   2022-01-31 01:02:03+08:00
# dtype: datetime64[ns, Asia/Taipei]

from numpy import nan
time_column = pd.Series([None, nan, '', float('inf'), float('-inf'), '110/12/31T00:12:21'])
convert_str_to_time_format(time_column, from_format='%TY/%m/%dT%H:%M:%S')
# Output:
# 0                         NaT
# 1                         NaT
# 2                         NaT
# 3                         NaT
# 4                         NaT
# 5   2021-12-31 00:12:21+08:00
# dtype: datetime64[ns, Asia/Taipei]

time_column = pd.Series(['110/12/31 00:12:21', '111/1/31 01:02:03'])
convert_str_to_time_format(time_column, from_format='%TY/%m/%d %H:%M:%S', is_from_utc=True)
# Output:
# 0   2021-12-31 08:12:21+08:00
# 1   2022-01-31 09:02:03+08:00
# dtype: datetime64[ns, Asia/Taipei]

time_column = pd.Series(['110/12/31', '111/1/31'])
date_col = convert_str_to_time_format(time_column, from_format='%TY/%m/%d', output_level='date')
print(date_col)
# Output
# 0    2021-12-31
# 1    2022-01-31
# dtype: object
print(type(date_col.iloc[0]))
# Output:
# <class 'datetime.date'>

time_column = pd.Series(['110/12/31', '111/1/31'])
str_datetime_col = convert_str_to_time_format(
    time_column, from_format='%TY/%m/%d', output_type='str'
)
print(str_datetime_col)
# >>> print(str_datetime_col)
# 0    2021-12-31
# 1    2022-01-31
# dtype: object
print(type(str_datetime_col.iloc[0]))
# >>> print(type(str_datetime_col.iloc[0]))
# <class 'str'>
```

### -函式 omit_chinese_string_in_time(x)

清除時間欄位中包含的"上下"或"下午"文字。

```python
import pandas as pd
from utils.transform_time import omit_chinese_string_in_time
omit_chinese_string_in_time(None)
# Output:
omit_chinese_string_in_time("2022/7/14 上午 12:00:00")
# Output: '2022-07-14 12:00:00'
omit_chinese_string_in_time("2022/7/14 下午 12:00:00")
# Output: '2022-07-14 00:00:00'
omit_chinese_string_in_time("2022/7/14 下午 12:00:00.000")
# Output: '2022-07-14 12:00:00'
```
