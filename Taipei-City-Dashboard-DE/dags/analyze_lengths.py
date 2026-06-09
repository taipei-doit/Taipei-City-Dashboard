import json
import urllib.request
import pandas as pd
import numpy as np
import sys

def mapping_category_ignore_number(string, cate):
    try:
        return cate[string]
    except KeyError:
        return string

print("Starting analysis...")
url = "https://tcgbusfs.blob.core.windows.net/blobtcmsv/TCMSV_alldesc.json"
try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read())
except Exception as e:
    print(f"Error downloading or parsing JSON: {e}")
    sys.exit(1)

print("Downloaded JSON successfully.")
raw_data = pd.DataFrame(res["data"]["park"])
data = raw_data.copy()
data.columns = data.columns.str.lower()
col_map = {
    "id": "station_id",
    "area": "dist",
    "name": "name",
    "type": "data_return_type",
    "type2": "owner_type",
}
data = data.rename(columns=col_map)

# Mappings
cate_map_type = {"1": "動態回傳剩餘車位數", "2": "靜態"}
data["data_return_type_mapped"] = data["data_return_type"].apply(mapping_category_ignore_number, cate=cate_map_type)

print("\n--- Data Return Type Analysis ---")
unique_vals = data['data_return_type'].unique()
print(f"Unique unmapped values: {unique_vals}")
unique_mapped = data['data_return_type_mapped'].unique()
print(f"Unique mapped values: {unique_mapped}")

for val in unique_mapped:
    str_val = str(val)
    print(f"Value: '{str_val}', Length: {len(str_val)}")

len_counts = data['data_return_type_mapped'].astype(str).str.len()
print(f"Max length found in data mapped return type: {len_counts.max()}")
if len_counts.max() > 10:
    print("Found values > 10!")
    long_values = data.loc[len_counts > 10, 'data_return_type_mapped'].unique()
    print(f"Long values: {long_values}")

