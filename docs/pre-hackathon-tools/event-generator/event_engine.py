#!/usr/bin/env python3
import json
import time
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- Configuration ---
# In a real hackathon, you'd point this to your cleaned data
STATIC_DATA_PATH = "static_labor_data.json"
EVENTS_PATH = "active_events.json"

def load_json(path, default=[]):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Logic: The "Drama" Merger ---
def apply_events(static_list, active_events):
    live_data = []
    
    for item in static_list:
        new_item = item.copy()
        district = item.get("District")
        
        for event in active_events:
            # Check if event targets this district
            target = event.get("target", {})
            if target.get("district") == district or target.get("district") == "ALL":
                # Apply impact (Multipliers or Additions)
                impact = event.get("impact", {})
                
                # Example: Multiplier impact
                if "unemployment_rate_mul" in impact:
                    # Logic assumes item has a base value
                    base = item.get("Unemployed", 0)
                    new_item["Unemployed"] = int(base * impact["unemployment_rate_mul"])
                    new_item["Event_Notice"] = event.get("title", "Event Active")
                
                # Example: Simple addition
                if "welfare_demand_add" in impact:
                    base = item.get("Welfare_Demand", 0)
                    new_item["Welfare_Demand"] = base + impact["welfare_demand_add"]

        live_data.append(new_item)
    return live_data

# --- API Endpoints ---
@app.route('/live-data', methods=['GET'])
def get_live_data():
    static_data = load_json(STATIC_DATA_PATH, [
        {"District": "內湖區", "Unemployed": 400, "Welfare_Demand": 50},
        {"District": "大安區", "Unemployed": 300, "Welfare_Demand": 40},
        {"District": "南港區", "Unemployed": 200, "Welfare_Demand": 30}
    ])
    events = load_json(EVENTS_PATH, [])
    
    live = apply_events(static_data, events)
    return jsonify({
        "timestamp": time.time(),
        "active_events_count": len(events),
        "data": live
    })

@app.route('/trigger-event', methods=['POST'])
def trigger_event():
    event = request.json
    events = load_json(EVENTS_PATH, [])
    events.append(event)
    save_json(EVENTS_PATH, events)
    return jsonify({"status": "Event Triggered", "event": event})

@app.route('/clear-events', methods=['POST'])
def clear_events():
    save_json(EVENTS_PATH, [])
    return jsonify({"status": "All Events Cleared"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5051, debug=True)
