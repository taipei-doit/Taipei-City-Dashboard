import json
import urllib.request
import pandas as pd
import numpy as np

url = "https://tcgbusfs.blob.core.windows.net/blobtcmsv/TCMSV_alldesc.json"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    res = json.loads(response.read())

raw_data = pd.DataFrame(res["data"]["park"])

def mapping_category_ignore_number(string, cate):
    try:
        return cate[string]
    except KeyError:
        return string

cate_map_type = {"1": "動態回傳剩餘車位數", "2": "靜態"}
data_return_type_mapped = raw_data['type'].apply(mapping_category_ignore_number, cate=cate_map_type)

print("Checking for trailing spaces in mapped values...")
for val in data_return_type_mapped.unique():
    str_val = str(val)
    if str_val.strip() != str_val:
        print(f"Value '{str_val}' HAS trailing/leading spaces! Original length: {len(str_val)}")
    else:
        print(f"Value '{str_val}' is clean. Length: {len(str_val)}")

print("\nChecking raw values of 'type' for anything unexpected...")
print(raw_data['type'].unique())
