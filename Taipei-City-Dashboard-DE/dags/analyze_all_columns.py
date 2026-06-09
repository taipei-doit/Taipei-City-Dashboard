import json
import urllib.request
import pandas as pd
import numpy as np

url = "https://tcgbusfs.blob.core.windows.net/blobtcmsv/TCMSV_alldesc.json"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    res = json.loads(response.read())

raw_data = pd.DataFrame(res["data"]["park"])
print(f"Total rows: {len(raw_data)}")

# Map columns like in the DAG
col_map = {
    "id": "station_id",
    "area": "dist",
    "name": "name",
    "type": "data_return_type",
    "type2": "owner_type",
    "summary": "summary",
    "address": "addr",
    "tel": "tel",
    "payex": "pay_info",
    "servicetime": "opening_time",
    "fareinfo": "fare_info",
    "entrancecoord": "entrance_coord",
}
data = raw_data.rename(columns=col_map)

# Add mapping logic
def mapping_category_ignore_number(string, cate):
    try:
        return cate[string]
    except KeyError:
        return string

cate_map_type = {"1": "動態回傳剩餘車位數", "2": "靜態"}
data["data_return_type"] = data["data_return_type"].apply(mapping_category_ignore_number, cate=cate_map_type)

cate_map_owner = {"1": "停管處經營", "2": "非停管處經營"}
data["owner_type"] = data["owner_type"].apply(mapping_category_ignore_number, cate=cate_map_owner)

for col in data.columns:
    max_len = data[col].astype(str).str.len().max()
    print(f"Column '{col}': max length {max_len}")
    if max_len == 10:
        example = data[col].astype(str).loc[data[col].astype(str).str.len() == 10].unique()
        print(f"  Example values with length 10: {example[:3]}")
    if max_len > 10:
        example = data[col].astype(str).loc[data[col].astype(str).str.len() > 10].unique()
        print(f"  Example values with length > 10: {example[:3]}")

