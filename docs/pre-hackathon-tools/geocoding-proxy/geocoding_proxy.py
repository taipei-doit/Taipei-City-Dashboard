#!/usr/bin/env python3
import sqlite3
import hashlib
import time
import os
import ssl
import certifi
from flask import Flask, request, jsonify
from flask_cors import CORS
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# --- Patch for macOS SSL issue ---
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

app = Flask(__name__)
CORS(app)

# --- Configuration ---
DB_PATH = "geocache.db"
USER_AGENT = "TaipeiDashdorad_Hackathon_Proxy"
# Default to Nominatim (OSM), but logic can be extended for Google Maps
DEFAULT_PROVIDER = "nominatim"

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS geocache (
            hash TEXT PRIMARY KEY,
            address TEXT,
            lat REAL,
            lon REAL,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_cached_result(address_hash):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT lat, lon, status FROM geocache WHERE hash = ?", (address_hash,))
    row = c.fetchone()
    conn.close()
    return row

def save_to_cache(address, address_hash, lat, lon, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO geocache (hash, address, lat, lon, status) VALUES (?, ?, ?, ?, ?)",
              (address_hash, address, lat, lon, status))
    conn.commit()
    conn.close()

# --- Geocoding Logic ---
# Use certifi to ensure CA bundles are found on macOS
import ssl
import certifi
ctx = ssl.create_default_context(cafile=certifi.where())
geocoder = Nominatim(user_agent=USER_AGENT, ssl_context=ctx)

def do_geocode(address):
    address_hash = hashlib.sha256(address.strip().lower().encode()).hexdigest()
    
    # 1. Check Cache
    cached = get_cached_result(address_hash)
    if cached:
        lat, lon, status = cached
        if status == "OK":
            return {"lat": lat, "lon": lon, "status": "CACHED"}
        else:
            return {"status": status, "note": "Previously failed"}

    # 2. Call API (with basic rate limiting sleep)
    print(f"📡 API Requesting: {address}")
    try:
        time.sleep(1.0) # Nomitatim requires 1s between requests
        location = geocoder.geocode(address)
        if location:
            save_to_cache(address, address_hash, location.latitude, location.longitude, "OK")
            return {"lat": location.latitude, "lon": location.longitude, "status": "OK"}
        else:
            save_to_cache(address, address_hash, None, None, "NOT_FOUND")
            return {"status": "NOT_FOUND"}
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        return {"status": "ERROR", "message": str(e)}

# --- API Endpoints ---
@app.route('/geocode', methods=['GET'])
def geocode_endpoint():
    address = request.args.get('address')
    if not address:
        return jsonify({"error": "Missing address parameter"}), 400
    
    result = do_geocode(address)
    return jsonify(result)

@app.route('/batch', methods=['POST'])
def batch_geocode():
    data = request.json
    addresses = data.get('addresses', [])
    results = {}
    for addr in addresses:
        results[addr] = do_geocode(addr)
    return jsonify(results)

if __name__ == "__main__":
    init_db()
    # Using thread=False for SQLite compatibility in simple dev server
    app.run(host='0.0.0.0', port=5050, debug=True)
