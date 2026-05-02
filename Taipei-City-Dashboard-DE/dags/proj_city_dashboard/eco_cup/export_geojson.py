#!/usr/bin/env python3
"""
Export eco_cup_store from postgres-data to GeoJSON for frontend mapData.
"""

import json
import os

import psycopg2

POSTGRES_URI = os.environ.get(
    "POSTGRES_URI",
    "postgresql://postgres:postgres@localhost:5433/dashboard"
)
OUTPUT_PATH = os.environ.get(
    "OUTPUT_PATH",
    "Taipei-City-Dashboard-FE/public/mapData/eco_cup_store.geojson"
)


def main():
    conn = psycopg2.connect(POSTGRES_URI)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            brand,
            store_name,
            address,
            city,
            district,
            phone,
            lon,
            lat,
            ST_AsGeoJSON(wkb_geometry)::json AS geometry
        FROM eco_cup_store
        WHERE wkb_geometry IS NOT NULL;
    """)

    features = []
    for row in cur.fetchall():
        brand, store_name, address, city, district, phone, lon, lat, geom = row
        feature = {
            "type": "Feature",
            "properties": {
                "brand": brand,
                "store_name": store_name,
                "address": address,
                "city": city,
                "district": district,
                "phone": phone,
            },
            "geometry": geom,
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "name": "eco_cup_store",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        },
        "features": features,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"Exported {len(features)} features to {OUTPUT_PATH}")
    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    exit(main())
