import json
import ssl
import time
import os
import re
import certifi
import pandas as pd
from geopy.geocoders import ArcGIS
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPE_XLSX = os.path.join(BASE, "Taipei-City-Dashboard-DE/dags/utils/opendata/衛生餐廳/臺北市通過餐飲衛生管理分級評核名單.xlsx")
NTPC_XLSX = os.path.join(BASE, "Taipei-City-Dashboard-DE/dags/utils/opendata/衛生餐廳/新北市通過餐飲衛生管理分級名單.xlsx")
TPE_GEOJSON = os.path.join(BASE, "Taipei-City-Dashboard-FE/public/mapData/hygiene_restaurant_tpe.geojson")
NTPC_GEOJSON = os.path.join(BASE, "Taipei-City-Dashboard-FE/public/mapData/hygiene_restaurant_ntpc.geojson")
CACHE_FILE = os.path.join(BASE, "scripts/geocode_cache.json")

ctx = ssl.create_default_context(cafile=certifi.where())
geolocator = ArcGIS(ssl_context=ctx, timeout=10)

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        cache = json.load(f)
else:
    cache = {}


def geocode_address(addr):
    if addr in cache:
        return cache[addr]
    for attempt in range(3):
        try:
            result = geolocator.geocode(addr)
            if result:
                coords = [result.longitude, result.latitude]
                cache[addr] = coords
                return coords
            else:
                cache[addr] = None
                return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"  Retry {attempt+1} for: {addr} ({e})")
            time.sleep(2 ** attempt)
    cache[addr] = None
    return None


def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, ensure_ascii=False)


def xlsx_to_geojson(xlsx_path, geojson_path, label, city_regex):
    df = pd.read_excel(xlsx_path)
    total = len(df)
    success = 0
    fail = 0
    features = []

    for i, (_, row) in enumerate(df.iterrows()):
        addr = str(row.get("地址", "")).strip()
        name = str(row.get("店名", "")).strip()
        category = str(row.get("餐飲業別", "")).strip()
        grade = str(row.get("評核等級", "")).strip()
        tel = str(row.get("電話", "")).strip()

        match = re.search(city_regex, addr)
        district = match.group(1) if match else ""

        coords = geocode_address(addr)
        if coords:
            success += 1
        else:
            fail += 1
            print(f"  FAIL: {addr}")

        feat = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": coords if coords else [0.0, 0.0],
            },
            "properties": {
                "name": name,
                "district": district,
                "category": category,
                "grade": grade,
                "tel": tel,
                "address": addr,
            },
        }
        features.append(feat)

        if (i + 1) % 10 == 0:
            print(f"  [{label}] {i+1}/{total} done (ok={success}, fail={fail})")
            save_cache()
        time.sleep(0.15)

    gj = {"type": "FeatureCollection", "features": features}
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False)

    print(f"[{label}] Finished: {success}/{total} geocoded, {fail} failed")
    save_cache()


print("=== Geocoding TPE ===")
xlsx_to_geojson(TPE_XLSX, TPE_GEOJSON, "TPE", r"[台臺]北市(\S{2,3}區)")

print("\n=== Geocoding NTPC ===")
xlsx_to_geojson(NTPC_XLSX, NTPC_GEOJSON, "NTPC", r"新北市(\S{2,3}區)")

print(f"\nCache size: {len(cache)} entries")
print("Done.")
