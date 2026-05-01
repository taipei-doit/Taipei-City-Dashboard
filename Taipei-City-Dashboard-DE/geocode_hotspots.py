"""
Reverse-geocode the top hotspots via Nominatim and write near_location back to DB.
Run from inside Docker on br_dashboard network:

docker run --rm --network br_dashboard \
  -v "C:/Users/tinti/Desktop/Taipei-City-Dashboard/Taipei-City-Dashboard-DE:/etl" \
  -w /etl python:3.12-slim \
  bash -c "pip install -q requests sqlalchemy psycopg2-binary && python geocode_hotspots.py"
"""

import os
import time
import requests
from sqlalchemy import create_engine, text

DB_URI = (
    f"postgresql://{os.environ.get('DB_USER','postgres')}"
    f":{os.environ.get('DB_PASSWORD','lja2203125')}"
    f"@{os.environ.get('DB_HOST','postgres-data')}"
    f":{os.environ.get('DB_PORT','5432')}"
    f"/{os.environ.get('DB_NAME','dashboard')}"
)

HEADERS = {"User-Agent": "taipei-city-dashboard-hackathon/1.0"}

def reverse_geocode(lat: float, lng: float) -> str:
    url = (
        f"https://nominatim.openstreetmap.org/reverse"
        f"?lat={lat}&lon={lng}&format=json&zoom=17&accept-language=zh-TW"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        d = r.json()
        addr = d.get("address", {})
        # 優先取路名，再取地標
        road = (
            addr.get("road")
            or addr.get("pedestrian")
            or addr.get("path")
            or addr.get("suburb")
            or d.get("display_name", "").split(",")[0]
        )
        district = addr.get("city_district") or addr.get("suburb") or ""
        if district and district not in road:
            return f"{district}{road}"
        return road
    except Exception as e:
        print(f"  geocode error ({lat},{lng}): {e}")
        return ""

def main():
    engine = create_engine(DB_URI)

    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id, center_lat, center_lng FROM traffic_pedestrian_hotspot "
            "ORDER BY accident_count DESC LIMIT 30"
        )).fetchall()

    print(f"Geocoding top {len(rows)} hotspots...")
    updates = []
    for i, row in enumerate(rows):
        hid, lat, lng = row.id, row.center_lat, row.center_lng
        name = reverse_geocode(lat, lng)
        print(f"  [{i+1:02d}] ({lat:.3f},{lng:.3f}) → {name}")
        updates.append({"hid": hid, "name": name})
        time.sleep(1.1)  # Nominatim 1 req/sec limit

    with engine.begin() as conn:
        for u in updates:
            conn.execute(
                text("UPDATE traffic_pedestrian_hotspot SET near_location=:n WHERE id=:i"),
                {"n": u["name"], "i": u["hid"]}
            )

    print(f"Updated {len(updates)} rows.")

if __name__ == "__main__":
    main()
