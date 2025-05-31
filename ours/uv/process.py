# target output:
# StationName
# StationId
# ObsTime
# GeoInfo
# WeatherElement

import json
import pandas as pd

with open("uv.json", "r") as f:
    data = json.load(f)
    
    

df = pd.DataFrame()
for station in data["records"]["Station"]:
    # more cities to show better accuracy
    if station["GeoInfo"]["CountyName"] not in ["臺北市", "新北市", "基隆市", "桃園市"]:
        continue
    
    # todo: check
    if station["WeatherElement"]["UVIndex"] == "-99":
        print("no data of station: ", station["StationName"])
        # continue
     
    

    new_row = pd.DataFrame([{
        "StationName": station["StationName"],
        "StationId": station["StationId"],
        "ObsTime": station["ObsTime"]["DateTime"],
        "Lat": station["GeoInfo"]["Coordinates"][1]["StationLatitude"],
        "Lon": station["GeoInfo"]["Coordinates"][1]["StationLongitude"],
        "District": station["GeoInfo"]["TownName"],
        "City": station["GeoInfo"]["CountyName"],
        "DistrictCode": station["GeoInfo"]["TownCode"],
        "CityCode": station["GeoInfo"]["CountyCode"],
        "UVIndex": station["WeatherElement"]["UVIndex"],
    }])
    df = pd.concat([df, new_row], ignore_index=True)

df.to_csv("uv.csv", index=False)
    

# csv2geojson --lon Lon --lat Lat uv_taipei_fake.csv   > uv_taipei.geojson