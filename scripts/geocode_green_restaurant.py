import json
import ssl
import time
import os
import certifi
from geopy.geocoders import ArcGIS
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPE_GEOJSON = os.path.join(BASE, "Taipei-City-Dashboard-FE/public/mapData/green_restaurant_tpe.geojson")
NTPC_GEOJSON = os.path.join(BASE, "Taipei-City-Dashboard-FE/public/mapData/green_restaurant_ntpc.geojson")
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

def process_geojson(path, label):
    with open(path) as f:
        gj = json.load(f)

    total = len(gj["features"])
    success = 0
    fail = 0

    for i, feat in enumerate(gj["features"]):
        addr = feat["properties"]["address"]
        coords = geocode_address(addr)
        if coords:
            feat["geometry"]["coordinates"] = coords
            success += 1
        else:
            fail += 1
            print(f"  FAIL: {addr}")

        if (i + 1) % 50 == 0:
            print(f"  [{label}] {i+1}/{total} done (ok={success}, fail={fail})")
            save_cache()
        time.sleep(0.15)

    with open(path, "w") as f:
        json.dump(gj, f, ensure_ascii=False)

    print(f"[{label}] Finished: {success}/{total} geocoded, {fail} failed")
    save_cache()
    return gj

print("=== Geocoding TPE ===")
tpe_gj = process_geojson(TPE_GEOJSON, "TPE")

print("\n=== Geocoding NTPC ===")
ntpc_gj = process_geojson(NTPC_GEOJSON, "NTPC")

print(f"\nCache size: {len(cache)} entries")
print("Done.")
