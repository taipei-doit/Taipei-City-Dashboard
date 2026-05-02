import json
import subprocess

GEOJSON = "/Users/fiona930607/Desktop/Taipei-City-Dashboard/Taipei-City-Dashboard-FE/public/mapData/hygiene_restaurant_ntpc.geojson"

with open(GEOJSON) as f:
    gj = json.load(f)

sql_lines = []
sql_lines.append("BEGIN;")
sql_lines.append("DELETE FROM hygiene_restaurant_ntpc;")

for feat in gj["features"]:
    props = feat["properties"]
    coords = feat["geometry"]["coordinates"]
    lng, lat = coords[0], coords[1]

    def esc(v):
        if v is None:
            return "NULL"
        return "'" + str(v).replace("'", "''") + "'"

    wkb = f"ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)"

    sql_lines.append(
        f"INSERT INTO hygiene_restaurant_ntpc (district, name, category, grade, tel, address, longitude, latitude, wkb_geometry) "
        f"VALUES ({esc(props.get('district'))}, {esc(props.get('name'))}, {esc(props.get('category'))}, "
        f"{esc(props.get('grade'))}, {esc(props.get('tel'))}, {esc(props.get('address'))}, "
        f"{lng}, {lat}, {wkb});"
    )

sql_lines.append("COMMIT;")
sql = "\n".join(sql_lines)

result = subprocess.run(
    ["docker", "exec", "-i", "postgres-data", "psql", "-U", "postgres", "-d", "dashboard"],
    input=sql, capture_output=True, text=True
)
lines = result.stdout.strip().split('\n')
print(f"Total output lines: {len(lines)}")
print("Last line:", lines[-1] if lines else "empty")
if result.returncode != 0:
    print("ERROR:", result.stderr[-500:])
else:
    print("Success!")
