import geopandas as gpd
import json
import os
import pandas as pd
from shapely.geometry import Polygon

building_df = pd.read_csv("./public/csv/危樓經緯度.csv")

output_file = "./public/chartData/666.json"
output_dict = {}
summed_df = building_df.groupby("行政區")["面積"].sum().reset_index()
df = summed_df[["行政區", "面積"]].rename(columns={"行政區": "x", "面積": "y"})

output_dict["data"] = [{"name": "危樓總面積"}, {"data": df.to_dict(orient="records")}]
with open(output_file, "w", encoding="utf-8") as file:
    json.dump(output_dict, file, ensure_ascii=False, indent=4)
